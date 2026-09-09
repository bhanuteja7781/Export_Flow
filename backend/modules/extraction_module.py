"""
extraction_module.py - Tiered Lead Data Extraction & Scoring Engine
Refactored to prioritize high-value decision-makers and procurement contacts
without discarding generic inboxes, using a 3-tier classification & confidence scoring model.
"""

import re
import uuid
import datetime
from typing import List, Dict, Any, Optional, Tuple


class DataExtractionModule:
    """
    Tiered Lead Data Extraction, Scoring, and Normalization Engine.
    """

    EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.css', '.js')

    # Common personal first names for name inference & named mailbox detection
    COMMON_FIRST_NAMES = {
        'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'joseph',
        'thomas', 'charles', 'christopher', 'daniel', 'matthew', 'anthony', 'donald',
        'mark', 'paul', 'steven', 'andrew', 'kenneth', 'joshua', 'george', 'kevin',
        'brian', 'edward', 'ronald', 'timothy', 'jason', 'jeffrey', 'ryan', 'jacob',
        'gary', 'nicholas', 'eric', 'jonathan', 'stephen', 'larry', 'justin', 'scott',
        'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan',
        'jessica', 'sarah', 'karen', 'nancy', 'lisa', 'betty', 'margaret', 'sandra',
        'ashley', 'kimberly', 'emily', 'donna', 'michelle', 'carol', 'amanda', 'melissa',
        'deborah', 'stephanie', 'rebecca', 'laura', 'sharon', 'cynthia', 'kathleen',
        'amy', 'shirley', 'angela', 'helen', 'anna', 'brenda', 'pamela', 'nicole',
        'emma', 'samantha', 'katherine', 'christine', 'debra', 'rachel', 'catherine',
        'carolyn', 'janet', 'ruth', 'maria', 'heather', 'diane', 'virginia', 'julie',
        'joyce', 'victoria', 'olivia', 'kelly', 'christina', 'lauren', 'joan', 'evelyn',
        'judith', 'megan', 'cheryl', 'andrea', 'hannah', 'martha', 'jacqueline', 'frances',
        'rajesh', 'priya', 'amit', 'rahul', 'anita', 'sunil', 'deepak', 'pooja', 'vikram',
        'sanjay', 'neha', 'suresh', 'alok', 'rohit', 'kavita', 'manoj', 'arun', 'geeta',
        'ravi', 'swati', 'vivek', 'sandhya', 'tarun', 'divya', 'ajay', 'meera', 'nilesh'
    }

    # Tier 1 Functional Procurement Prefixes
    TIER1_PROCUREMENT_PREFIXES = [
        'procurement', 'sourcing', 'tenders', 'tender', 'vendor-desk', 'vendordesk',
        'purchasing', 'purchase', 'buying', 'buyer', 'buyers', 'category-buyer',
        'categorybuyer', 'merchandising', 'merchandiser', 'supplychain', 'supply-chain',
        'vendorinquiries', 'vendor-inquiries', 'vendorrelations', 'vendor-relations',
        'supplierdesk', 'supplier-desk', 'imports', 'importing', 'trade'
    ]

    # Tier 1 Role Keywords (within 200 characters)
    TIER1_ROLE_KEYWORDS = [
        'procurement', 'sourcing', 'purchasing', 'purchase', 'supply chain', 'supplychain',
        'vendor management', 'vendor onboarding', 'vendor desk', 'vendor relations',
        'category buyer', 'category buying', 'tender invitee', 'tenders', 'tender',
        'purchase officer', 'merchandiser', 'merchandising', 'buying director',
        'head of buying', 'chief procurement officer', 'sourcing manager', 'import manager',
        'supplier relations', 'supplier desk', 'suppliers', 'supplier', 'trade buyer',
        'director of procurement', 'vp procurement', 'procurement lead', 'procurement desk',
        'supplier inquiries', 'vendor inquiries'
    ]

    # Tier 2 Departmental / Leadership Prefixes
    TIER2_DEPARTMENT_PREFIXES = [
        'partnerships', 'partnership', 'partners', 'partner', 'operations', 'corporate',
        'leadership', 'management', 'founder', 'co-founder', 'director', 'managing-director',
        'president', 'ceo', 'coo', 'vp', 'executive', 'commercial', 'contract',
        'showroom', 'studio', 'storemanager', 'owner', 'proprietor'
    ]

    # Tier 2 Role Keywords (within 200 characters)
    TIER2_ROLE_KEYWORDS = [
        'founder', 'co-founder', 'owner', 'proprietor', 'president', 'managing director',
        'director', 'vice president', 'chief operating officer', 'operations manager',
        'commercial director', 'general manager', 'showroom manager', 'principal designer',
        'partner', 'headquarters', 'executive team'
    ]

    # Tier 3 Broad / Service Prefixes
    TIER3_SERVICE_PREFIXES = [
        'info', 'support', 'care', 'customercare', 'help', 'contact', 'hello',
        'inquiries', 'inquiry', 'general', 'mail', 'office', 'admin', 'team',
        'sales', 'orders', 'service', 'services', 'desk'
    ]

    # Absolute Excluded Email Patterns (Internal/System/Spam)
    DISQUALIFIED_PATTERNS = [
        'customerservice', 'custserv', 'clientcare', 'consumer', 'returns',
        'billing', 'accounting', 'invoice', 'accounts', 'payables', 'receivables',
        'jobs', 'careers', 'recruiting', 'hiring', 'hr', 'media', 'press', 'pr',
        'privacy', 'legal', 'compliance', 'unsubscribe', 'newsletter', 'noreply',
        'no-reply', 'donotreply', 'guestservices', 'frontdesk', 'reservations',
        'booking', 'reception', 'abuse', 'postmaster', 'hostmaster', 'webmaster'
    ]

    def __init__(self):
        pass

    def _is_disqualified_email(self, email: str) -> bool:
        if not email or '@' not in email:
            return True
        email_clean = email.strip().lower()
        prefix = email_clean.split('@')[0].replace('.', '').replace('-', '').replace('_', '')

        # Whitelist all Tier 1 Procurement & Sourcing prefixes unconditionally
        for proc in self.TIER1_PROCUREMENT_PREFIXES:
            proc_clean = proc.replace('.', '').replace('-', '').replace('_', '')
            if prefix == proc_clean or prefix.startswith(proc_clean):
                return False

        for disq in self.DISQUALIFIED_PATTERNS:
            disq_clean = disq.replace('.', '').replace('-', '').replace('_', '')
            if len(disq_clean) <= 3:
                if prefix == disq_clean:
                    return True
            else:
                if prefix == disq_clean or prefix.startswith(disq_clean):
                    return True
        return False

    GENERIC_ROLE_PREFIXES = {
        'vendor-desk', 'vendordesk', 'category-buyer', 'categorybuyer', 'supply-chain', 'supplychain',
        'vendor-inquiries', 'vendorinquiries', 'vendor-relations', 'vendorrelations', 'supplier-desk',
        'supplierdesk', 'managing-director', 'co-founder', 'store-manager', 'storemanager',
        'general-inquiries', 'customer-care', 'customercare', 'customer-service', 'customerservice',
        'trade-desk', 'tradedesk', 'procurement-team', 'purchasing-team', 'sourcing-team'
    }

    def _is_named_individual_prefix(self, prefix: str) -> Tuple[bool, Optional[str]]:
        """
        Detects if email prefix matches personal naming patterns:
        - firstname.lastname, firstname_lastname, firstname-lastname
        - f.lastname, flastname
        - standalone known first names (e.g. sarah, john, rajesh)
        """
        clean = prefix.lower().strip()

        # Disqualify known generic role and department prefixes
        if clean in self.GENERIC_ROLE_PREFIXES:
            return False, None
        if any(clean == p or clean.startswith(p) for p in self.TIER1_PROCUREMENT_PREFIXES + self.TIER2_DEPARTMENT_PREFIXES + self.TIER3_SERVICE_PREFIXES):
            return False, None

        # Check firstname.lastname / firstname_lastname / firstname-lastname
        parts = re.split(r'[\._\-]', clean)
        if len(parts) == 2 and all(p.isalpha() for p in parts) and len(parts[0]) >= 2 and len(parts[1]) >= 2:
            first = parts[0].capitalize()
            last = parts[1].capitalize()
            return True, f"{first} {last}"

        # Check initial.lastname (e.g., s.jenkins or s_jenkins)
        if len(parts) == 2 and len(parts[0]) == 1 and parts[0].isalpha() and len(parts[1]) >= 2 and parts[1].isalpha():
            return True, f"{parts[0].upper()}. {parts[1].capitalize()}"

        # Check standalone first name
        if clean in self.COMMON_FIRST_NAMES:
            return True, clean.capitalize()

        return False, None

    def _extract_context_window(self, text: str, email: str, window_size: int = 200) -> str:
        """
        Extracts up to `window_size` characters before and after the email occurrence in text.
        """
        if not text or not email:
            return ""
        idx = text.lower().find(email.lower())
        if idx == -1:
            return text[:window_size * 2]
        start = max(0, idx - window_size)
        end = min(len(text), idx + len(email) + window_size)
        return text[start:end]

    def _extract_adjacent_name(self, context_window: str, email: str) -> Optional[str]:
        """
        Attempts to find a human name adjacent to the email in the context window.
        """
        # Patterns like "Contact: Sarah Jenkins", "Attn: John Smith", "Buyer: Priya Sharma"
        patterns = [
            r'(?:contact|attn|buyer|sourcing|procurement|manager|lead|name)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,\s*(?:procurement|sourcing|buyer|purchasing|director|manager|founder|owner)',
            r'(?:hi|hello|regards|sincerely|warmly)\s*,\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        for pat in patterns:
            match = re.search(pat, context_window, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Filter out generic titles mistakenly matched
                if not any(gen in extracted.lower() for gen in ['purchasing team', 'procurement desk', 'customer service', 'sales department']):
                    return extracted
        return None

    def _infer_job_title_or_context(
        self,
        context_window: str,
        email_prefix: str,
        lead_tier: str,
        source_url: str = ""
    ) -> str:
        """
        Determines the specific job title or page context for the lead.
        """
        ctx_lower = context_window.lower()
        url_lower = source_url.lower()

        # Check direct procurement role matches
        for kw in self.TIER1_ROLE_KEYWORDS:
            if kw in ctx_lower:
                return kw.title()

        # Check URL paths
        if any(p in url_lower for p in ['/procurement', '/vendors', '/suppliers', '/vendor-registration']):
            return "Vendor / Procurement Desk"
        if any(p in url_lower for p in ['/tenders', '/rfps', '/bids']):
            return "Tender & Bids Desk"
        if any(p in url_lower for p in ['/leadership', '/management', '/team', '/about-us']):
            return "Leadership & Executive Team"
        if any(p in url_lower for p in ['/wholesale', '/trade']):
            return "Wholesale & Trade Division"

        # Check leadership role matches
        for kw in self.TIER2_ROLE_KEYWORDS:
            if kw in ctx_lower:
                return kw.title()

        # Check prefix hints
        if email_prefix in self.TIER1_PROCUREMENT_PREFIXES:
            return f"Purchasing & Sourcing ({email_prefix.title()})"
        if email_prefix in self.TIER2_DEPARTMENT_PREFIXES:
            return f"Departmental ({email_prefix.title()})"
        if email_prefix in ['sales', 'orders']:
            return "Commercial Sales / Trade Desk"
        if email_prefix in ['contact', 'info', 'hello']:
            return "General Store Inquiries"

        if lead_tier.startswith("Tier 1"):
            return "Procurement Decision-Maker"
        if lead_tier.startswith("Tier 2"):
            return "Departmental Contact"
        return "Contact Page Footer"

    def classify_and_score_email(
        self,
        email: str,
        raw_text: str = "",
        source_url: str = "",
        page_title: str = ""
    ) -> Dict[str, Any]:
        """
        Implements the 3-tier classification & confidence scoring engine:
        - Tier 1: Target Decision-Makers & Procurement (Score: 0.75 - 1.00)
        - Tier 2: Secondary / Departmental Fallback (Score: 0.50 - 0.74)
        - Tier 3: Low Priority Broad / Service Inboxes (Score: 0.15 - 0.49)
        """
        email_clean = email.strip().lower()
        prefix = email_clean.split('@')[0]
        context_window = self._extract_context_window(raw_text, email_clean, window_size=200)
        local_context = f"{source_url} {context_window}".lower()

        # Check naming pattern
        is_named, inferred_name = self._is_named_individual_prefix(prefix)
        adjacent_name = self._extract_adjacent_name(context_window, email_clean)
        target_name = adjacent_name or inferred_name

        # Check keyword matches strictly within 200 chars or URL path
        has_procurement_keywords = any(kw in context_window.lower() for kw in self.TIER1_ROLE_KEYWORDS)
        has_procurement_prefix = any(p == prefix or prefix.startswith(p) for p in self.TIER1_PROCUREMENT_PREFIXES)

        has_leadership_keywords = any(kw in context_window.lower() for kw in self.TIER2_ROLE_KEYWORDS)
        has_department_prefix = any(p == prefix or prefix.startswith(p) for p in self.TIER2_DEPARTMENT_PREFIXES)

        is_procurement_url = any(p in source_url.lower() for p in ['/procurement', '/vendors', '/suppliers', '/vendor-registration', '/tenders', '/rfps'])
        is_leadership_url = any(p in source_url.lower() for p in ['/leadership', '/management', '/team', '/about-us', '/about'])

        # -------------------------------------------------------------
        # Tier 1: High Priority (Target Decision-Makers & Procurement)
        # -------------------------------------------------------------
        if has_procurement_prefix and has_procurement_keywords:
            lead_tier = "Tier 1 - Procurement/Individual"
            confidence_score = 0.98
        elif is_named and (has_procurement_keywords or (adjacent_name and is_procurement_url)):
            lead_tier = "Tier 1 - Procurement/Individual"
            confidence_score = 0.93
        elif has_procurement_prefix:
            lead_tier = "Tier 1 - Procurement/Individual"
            confidence_score = 0.88
        elif has_procurement_keywords and not (prefix in self.TIER3_SERVICE_PREFIXES):
            lead_tier = "Tier 1 - Procurement/Individual"
            confidence_score = 0.84
        elif is_named and (has_leadership_keywords or is_leadership_url):
            lead_tier = "Tier 1 - Procurement/Individual"
            confidence_score = 0.80
        elif is_named:
            # Named individual mailbox
            lead_tier = "Tier 1 - Procurement/Individual"
            confidence_score = 0.76

        # -------------------------------------------------------------
        # Tier 2: Secondary / Departmental (Fallback Leads)
        # -------------------------------------------------------------
        elif has_department_prefix or (has_leadership_keywords and prefix not in self.TIER3_SERVICE_PREFIXES):
            lead_tier = "Tier 2 - Secondary"
            confidence_score = 0.68
        elif (is_procurement_url and prefix not in self.TIER3_SERVICE_PREFIXES) or any(p in source_url.lower() for p in ['/partners', '/wholesale', '/trade']):
            lead_tier = "Tier 2 - Secondary"
            confidence_score = 0.62
        elif prefix in ['sales', 'orders', 'commercial']:
            lead_tier = "Tier 2 - Secondary"
            confidence_score = 0.58

        # -------------------------------------------------------------
        # Tier 3: Low Priority (Broad / Service Inboxes)
        # -------------------------------------------------------------
        else:
            lead_tier = "Tier 3 - Low Priority Generic"
            if prefix in ['contact', 'hello', 'inquiries']:
                confidence_score = 0.42
            elif prefix in ['info']:
                confidence_score = 0.35
            elif prefix in ['support', 'care', 'help']:
                confidence_score = 0.22
            else:
                confidence_score = 0.30

        job_title_or_context = self._infer_job_title_or_context(
            context_window=context_window,
            email_prefix=prefix,
            lead_tier=lead_tier,
            source_url=source_url
        )

        return {
            "email": email_clean,
            "lead_tier": lead_tier,
            "confidence_score": round(confidence_score, 2),
            "target_name": target_name,
            "job_title_or_context": job_title_or_context,
            "context_window": context_window
        }

    def _infer_company_name(self, raw_text: str, domain: str, title: str) -> str:
        """
        Infers clean company name from title or web domain.
        """
        junk_words = {
            "homepage", "home page", "home", "index", "member directory", "directory",
            "about us", "about", "contact us", "contact", "welcome", "amazon", "faire"
        }
        # Clean title first
        if title:
            cleaned_title = re.split(r'\s+[-–|—:]\s+', title)[0].strip()
            # If the first segment is junk, check subsequent segments
            if cleaned_title.lower() in junk_words:
                parts = re.split(r'\s+[-–|—:]\s+', title)
                cleaned_title = ""
                for p in parts[1:]:
                    p_clean = p.strip()
                    if p_clean and p_clean.lower() not in junk_words and len(p_clean) >= 3:
                        cleaned_title = p_clean
                        break

            # Remove trailing descriptors
            cleaned_title = re.sub(r'\b(Home Decor|Handicrafts|Wholesale|LLC|Inc|Ltd|Store|Shop)\b.*', r'\1', cleaned_title, flags=re.I).strip()
            if len(cleaned_title) >= 3 and cleaned_title.lower() not in junk_words and not any(ign in cleaned_title.lower() for ign in ['linkedin', 'instagram', 'facebook', 'google', 'search', 'email', 'contact']):
                return cleaned_title

        # Domain fallback
        clean_domain = domain.replace("www.", "").split(".")[0]
        return clean_domain.replace("-", " ").replace("_", " ").title()

    def _infer_country(self, raw_text: str, domain: str) -> str:
        text_lower = raw_text.lower()
        if domain.endswith(".ca") or any(prov in text_lower for prov in ["canada", "ontario", "toronto", "brampton", "mississauga", "vancouver", "surrey", "british columbia", "quebec", "montreal", "calgary", "alberta"]):
            return "Canada"
        return "United States"

    def _infer_city_state(self, raw_text: str, passed_city: str = "", passed_state: str = "") -> Tuple[str, str]:
        if passed_city and passed_state:
            return passed_city, passed_state

        text_lower = raw_text.lower()
        city = passed_city
        state = passed_state

        city_state_map = {
            'edison': ('Edison', 'New Jersey'),
            'iselin': ('Iselin', 'New Jersey'),
            'brampton': ('Brampton', 'Ontario'),
            'mississauga': ('Mississauga', 'Ontario'),
            'toronto': ('Toronto', 'Ontario'),
            'surrey': ('Surrey', 'British Columbia'),
            'vancouver': ('Vancouver', 'British Columbia'),
            'artesia': ('Artesia', 'California'),
            'fremont': ('Fremont', 'California'),
            'los angeles': ('Los Angeles', 'California'),
            'houston': ('Houston', 'Texas'),
            'dallas': ('Dallas', 'Texas'),
            'irving': ('Irving', 'Texas'),
            'chicago': ('Chicago', 'Illinois'),
            'atlanta': ('Atlanta', 'Georgia'),
            'new york': ('New York', 'New York'),
            'queens': ('Queens', 'New York'),
            'calgary': ('Calgary', 'Alberta'),
            'montreal': ('Montreal', 'Quebec'),
            'seattle': ('Seattle', 'Washington'),
            'miami': ('Miami', 'Florida'),
            'orlando': ('Orlando', 'Florida'),
            'columbus': ('Columbus', 'Ohio')
        }

        for k, (c, s) in city_state_map.items():
            if k in text_lower:
                return c, s

        return city or "Metropolitan Area", state or "North America"

    def extract_and_normalize(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts, ranks, and normalizes candidate leads across all items.
        Applies domain-level tier selection (retains Tier 3 only if Tier 1 & Tier 2 are absent),
        and returns records sorted by priority (`lead_tier` ASC, `confidence_score` DESC).
        """
        all_scored_leads: List[Dict[str, Any]] = []
        seen_emails = set()

        for item in raw_items:
            raw_text = item.get("raw_content", "") or item.get("title", "")
            source_url = item.get("url", "")
            source_platform = item.get("source_platform", "Web Search")
            passed_state = item.get("state", "")
            passed_city = item.get("city", "")
            passed_category = item.get("category", "")
            passed_size = item.get("buyer_size", "")
            passed_segment = item.get("market_segment", "")

            # 1. Discover all candidate emails in item
            candidate_emails = re.findall(self.EMAIL_PATTERN, raw_text)
            if item.get("email"):
                candidate_emails.insert(0, item["email"])

            # Clean and deduplicate candidates within this item
            item_candidates = []
            for em in candidate_emails:
                clean_em = em.strip().lower().rstrip('.,;:')
                if any(clean_em.endswith(ext) for ext in self.IMAGE_EXTENSIONS):
                    continue
                parts = clean_em.split('@')
                if len(parts) != 2 or len(parts[1]) > 50 or '.' not in parts[1]:
                    continue
                if self._is_disqualified_email(clean_em):
                    continue
                if clean_em not in item_candidates:
                    item_candidates.append(clean_em)

            if not item_candidates:
                continue

            # 2. Score and classify all candidate emails for this item
            scored_candidates = []
            for clean_em in item_candidates:
                score_meta = self.classify_and_score_email(
                    email=clean_em,
                    raw_text=raw_text,
                    source_url=source_url,
                    page_title=item.get("title", "")
                )
                scored_candidates.append(score_meta)

            # 3. Domain Tier Selection Logic:
            # If Tier 1 or Tier 2 leads exist for this item, suppress Tier 3 generic service inboxes.
            # Retain Tier 3 only if Tier 1 and Tier 2 are completely absent.
            has_tier1 = any(c["lead_tier"].startswith("Tier 1") for c in scored_candidates)
            has_tier2 = any(c["lead_tier"].startswith("Tier 2") for c in scored_candidates)

            if has_tier1 or has_tier2:
                eligible_candidates = [c for c in scored_candidates if not c["lead_tier"].startswith("Tier 3")]
            else:
                # Retain best Tier 3 candidates
                eligible_candidates = scored_candidates

            # 4. Build normalized lead records
            for candidate in eligible_candidates:
                clean_email = candidate["email"]
                if clean_email in seen_emails:
                    continue
                seen_emails.add(clean_email)

                domain_part = clean_email.split('@')[1]
                company_name = self._infer_company_name(raw_text, domain_part, item.get("title", ""))
                buyer_name = candidate["target_name"] or company_name
                website = source_url or f"https://www.{domain_part}"
                country = item.get("country") or self._infer_country(raw_text, domain_part)
                city, state = self._infer_city_state(raw_text, passed_city, passed_state)

                now_utc = datetime.datetime.now(datetime.timezone.utc)
                record = {
                    "id": item.get("id") or f"lead-{uuid.uuid4().hex[:8]}",
                    "date": item.get("date") or now_utc.strftime("%Y-%m-%d"),
                    "buyer_name": item.get("buyer_name") or candidate["target_name"] or company_name,
                    "target_name": candidate["target_name"],
                    "company_name": item.get("company_name") or company_name,
                    "email": clean_email,
                    "lead_tier": candidate["lead_tier"],
                    "confidence_score": candidate["confidence_score"],
                    "job_title_or_context": candidate["job_title_or_context"],
                    "source_url": website,
                    "website": item.get("website") or website,
                    "city": city,
                    "state": state,
                    "country": country,
                    "category": passed_category or item.get("category") or "home_decor_retailer",
                    "buyer_size": passed_size or item.get("buyer_size") or "independent_small",
                    "market_segment": passed_segment or item.get("market_segment") or "mid_range",
                    "source_platform": item.get("primary_source") or source_platform,
                    "validation_status": item.get("validation_status") or "valid",
                    "is_mx_verified": item.get("is_mx_verified", True),
                    "reply_status": item.get("reply_status") or "uncontacted",
                    "discovered_at": item.get("discovered_at") or now_utc.isoformat(),
                    "context_snippet": candidate["context_window"][:180],
                    # Multi-Source Transparency Fields
                    "primary_source": item.get("primary_source") or source_platform,
                    "discovery_sources": item.get("discovery_sources") or [item.get("primary_source") or source_platform],
                    "source_count": item.get("source_count") or len(item.get("discovery_sources") or [1]),
                    "social_profiles": item.get("social_profiles") or {},
                    "directory_profiles": item.get("directory_profiles") or [],
                    "source_urls": item.get("source_urls") or ([source_url] if source_url else []),
                    "cross_source_confidence": item.get("cross_source_confidence") or ("Very Strong" if len(item.get("discovery_sources", [])) >= 3 else ("Strong" if len(item.get("discovery_sources", [])) >= 2 else "Medium")),
                    "buyer_score": item.get("buyer_score") or int(float(candidate["confidence_score"]) * 100),
                    "product_compatibility": item.get("product_compatibility") or "High",
                    "business_authenticity": item.get("business_authenticity") or "High",
                    "score_breakdown": item.get("score_breakdown") or {}
                }
                all_scored_leads.append(record)

        # 5. Output Schema & Sorting:
        # Sort records in descending order of priority: `lead_tier` ASC, `confidence_score` DESC
        tier_weight = {
            "Tier 1 - Procurement/Individual": 1,
            "Tier 2 - Secondary": 2,
            "Tier 3 - Low Priority Generic": 3
        }

        all_scored_leads.sort(
            key=lambda l: (
                tier_weight.get(l.get("lead_tier"), 9),
                -float(l.get("confidence_score", 0.0))
            )
        )

        return all_scored_leads
