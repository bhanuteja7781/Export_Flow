"""
extraction_module.py - 5.2 Lead Data Extraction & Normalization Module
Extracts structured buyer metadata (buyer_name, company_name, email, website, country, source_platform)
from raw unstructured content from search engines, LinkedIn, social media, and B2B directories.
"""

import re
import uuid
import datetime
from typing import List, Dict, Any, Optional


class DataExtractionModule:
    """
    Normalizes raw search content into standard Buyer Records according to Algorithm 12.1.
    """

    EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.css', '.js')

    # Strictly Disqualified Consumer Support / Unrelated Inboxes
    DISQUALIFIED_EMAIL_PREFIXES = [
        'customerservice', 'customercare', 'custserv', 'service', 'services',
        'support', 'help', 'helpdesk', 'care', 'cs', 'clientservices', 'consumer',
        'returns', 'orders', 'shipping', 'billing', 'accounting', 'invoice', 'accounts',
        'payables', 'receivables', 'jobs', 'careers', 'recruiting', 'hiring', 'hr',
        'media', 'press', 'pr', 'privacy', 'legal', 'compliance', 'unsubscribe',
        'newsletter', 'noreply', 'no-reply', 'donotreply', 'marketing', 'guestservices',
        'frontdesk', 'reservations', 'booking', 'reception'
    ]

    # Commercial Wholesale, Trade & Sourcing (Priority: 100)
    WHOLESALE_TRADE_KEYWORDS = [
        'wholesale', 'trade', 'buyers', 'buyer', 'purchasing', 'procurement',
        'sourcing', 'merchandising', 'vendor', 'vendors', 'vendorinquiries',
        'buying', 'commercial', 'corporate', 'b2b', 'partners', 'partner',
        'supplier', 'suppliers', 'imports', 'import', 'contract', 'hospitality',
        'interiors', 'design'
    ]

    # Showroom & Store Locations (Priority: 90)
    SHOWROOM_STORE_KEYWORDS = [
        'showroom', 'store', 'shop', 'boutique', 'retail', 'gallery', 'studio', 'flagship',
        'locations', 'location', 'outlets', 'branch',
        'toronto', 'montreal', 'vancouver', 'calgary', 'ottawa', 'quebec', 'edmonton', 'winnipeg', 'halifax', 'victoria',
        'nyc', 'newyork', 'soho', 'brooklyn', 'chicago', 'la', 'losangeles', 'miami', 'dallas', 'seattle', 'boston',
        'austin', 'sanfrancisco', 'atlanta', 'houston', 'denver', 'scottsdale', 'phoenix', 'portland'
    ]

    # Leadership & HQ Inboxes (Priority: 75)
    LEADERSHIP_HQ_KEYWORDS = [
        'owner', 'founder', 'director', 'manager', 'president', 'headquarters',
        'office', 'hq', 'admin', 'info', 'contact', 'hello', 'team', 'inquiries', 'inquiry'
    ]

    def __init__(self):
        pass

    def _is_disqualified_email(self, email: str) -> bool:
        """
        Disqualifies consumer customer service, support desks, and non-commercial inboxes.
        """
        if not email or '@' not in email:
            return True
        prefix = email.split('@')[0].lower().replace('.', '').replace('-', '').replace('_', '')
        for disq in self.DISQUALIFIED_EMAIL_PREFIXES:
            disq_clean = disq.replace('.', '').replace('-', '').replace('_', '')
            if prefix == disq_clean or prefix.startswith(disq_clean):
                return True
        return False

    def _score_email_priority(self, email: str) -> int:
        """
        Scores email suitability for B2B commercial export outreach.
        Prioritizes Wholesale/Trade/Sourcing and Showroom locations over generic addresses.
        """
        if self._is_disqualified_email(email):
            return -100
        prefix = email.split('@')[0].lower()
        # 1. Wholesale / Trade / Sourcing / Procurement (Top Priority: 100)
        for kw in self.WHOLESALE_TRADE_KEYWORDS:
            if kw in prefix:
                return 100
        # 2. Direct Showroom / Store location (Priority: 90)
        for kw in self.SHOWROOM_STORE_KEYWORDS:
            if kw in prefix:
                return 90
        # 3. Leadership & HQ inboxes (Priority: 75)
        for kw in self.LEADERSHIP_HQ_KEYWORDS:
            if kw in prefix:
                return 75
        # 4. Personal named inboxes (sarah@, john.smith@: 60)
        return 60

    def extract_and_normalize(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes a list of raw search results and returns normalized lead dictionaries.
        Prioritizes direct showroom, store location, and sales department inboxes.
        """
        extracted_records = []
        seen_emails = set()

        for item in raw_items:
            raw_text = item.get("raw_content", "") or item.get("title", "")
            source_url = item.get("url", "")
            source_platform = item.get("source_platform", "Web Search")

            # 1. Regex candidate email extraction
            candidate_emails = re.findall(self.EMAIL_PATTERN, raw_text)

            # Clean and filter candidate emails
            cleaned_candidates = []
            for email in candidate_emails:
                clean_email = email.strip().lower().rstrip('.,;:')
                if any(clean_email.endswith(ext) for ext in self.IMAGE_EXTENSIONS):
                    continue
                parts = clean_email.split('@')
                if len(parts) != 2 or len(parts[1]) > 50:
                    continue
                if self._is_disqualified_email(clean_email):
                    continue
                cleaned_candidates.append(clean_email)

            # Sort by priority: Wholesale/Trade -> Showrooms/Stores -> Leadership/HQ -> Personal
            cleaned_candidates.sort(key=lambda em: self._score_email_priority(em), reverse=True)

            for clean_email in cleaned_candidates:
                domain_part = clean_email.split('@')[1]

                if clean_email in seen_emails:
                    continue
                seen_emails.add(clean_email)

                # 2. Extract context metadata
                buyer_name = self._infer_buyer_name(raw_text, clean_email, item.get("title", ""))
                company_name = self._infer_company_name(raw_text, domain_part, item.get("title", ""))
                website = source_url or f"https://www.{domain_part}"
                country = self._infer_country(raw_text, domain_part)

                now_utc = datetime.datetime.now(datetime.timezone.utc)
                record = {
                    "id": f"lead-{uuid.uuid4().hex[:8]}",
                    "date": now_utc.strftime("%Y-%m-%d"),
                    "buyer_name": buyer_name,
                    "company_name": company_name,
                    "email": clean_email,
                    "website": website,
                    "country": country,
                    "source_platform": source_platform,
                    "category": "unclassified",
                    "classification_reason": "",
                    "personalized_pitch": "",
                    "validation_status": "pending",
                    "validation_details": {},
                    "discovered_at": now_utc.isoformat(),
                    "last_contacted_at": None,
                    "approved": True,
                    "responses": "Pending Initial Outreach",
                    "intern_feedback": f"Prospective B2B candidate discovered from {source_platform}. Target for handcrafted metal candle holders & lanterns collection.",
                    "follow_ups": "Ready for initial catalog outreach dispatch"
                }
                extracted_records.append(record)

        return extracted_records

    def _infer_buyer_name(self, text: str, email: str, title: str = "") -> str:
        """
        Clean default buyer title without junk scraping artifacts.
        """
        return "Purchasing Team"

    def _infer_company_name(self, text: str, domain: str, title: str) -> str:
        """
        Infers business or store name from title or domain.
        """
        if title:
            # Clean title - split only on standalone dashes/separators with whitespace
            clean_title = re.split(r'\s+[-–|—]\s+|\s*:\s*', title)[0].strip()
            # Remove "LinkedIn" or generic descriptors
            clean_title = re.sub(r'\s*(?:on LinkedIn|Instagram|Facebook|Wholesale Buyer).*$', '', clean_title, flags=re.I).strip()
            if 3 < len(clean_title) < 50:
                return clean_title

        # Domain based
        base_domain = domain.split('.')[0].replace('-', ' ').title()
        return base_domain or "North America Buyer"

    def _infer_country(self, text: str, domain: str = "") -> str:
        """
        Infers country with precision for United States and Canada.
        """
        if domain.endswith(".ca"):
            return "Canada"
        if domain.endswith(".us"):
            return "United States"

        lower_text = text.lower()
        
        # Canadian Clues
        canadian_keywords = [
            "canada", "ontario", "toronto", "vancouver", "british columbia", "quebec",
            "montreal", "calgary", "alberta", "ottawa", "edmonton", "winnipeg", "manitoba",
            "nova scotia", "halifax", "victoria bc", ".ca"
        ]
        if any(kw in lower_text for kw in canadian_keywords):
            return "Canada"

        # US Clues
        us_keywords = [
            "united states", "usa", "u.s.a", "california", "new york", "texas",
            "florida", "illinois", "chicago", "los angeles", "georgia", "colorado",
            "massachusetts", "north carolina", "ohio", "washington", "seattle"
        ]
        if any(kw in lower_text for kw in us_keywords):
            return "United States"

        return "United States"
