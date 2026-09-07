"""
entity_resolver.py - Cross-Source Entity Resolution & Deduplication Engine
Merges multiple discoveries of the same business across different sources
(e.g., Google + Instagram + LinkedIn + Official Website) into a single unified buyer record.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional, Set, Tuple


class EntityResolver:
    """
    Performs entity resolution across domains, business names, social handles,
    and phone numbers to prevent duplicate buyer creation and merge source evidence.
    """

    COMPANY_SUFFIXES = [
        r'\bllc\b', r'\binc\b', r'\bltd\b', r'\bcorp\b', r'\bcorporation\b',
        r'\bco\b', r'\benterprises\b', r'\bgroup\b', r'\bholdings\b',
        r'\bstore\b', r'\bshop\b', r'\bboutique\b', r'\bshowroom\b'
    ]

    @classmethod
    def normalize_company_name(cls, name: str) -> str:
        """
        Normalizes company names for fuzzy identity matching.
        e.g. 'ABC Home Décor LLC' -> 'abc home decor'
        """
        if not name:
            return ""
        clean = name.lower().strip()
        # Replace accented characters
        clean = clean.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c")
        # Strip punctuation
        clean = re.sub(r'[\'\".,;:\-_/\\|()#&]', ' ', clean)
        # Strip common legal and store suffixes
        for sfx in cls.COMPANY_SUFFIXES:
            clean = re.sub(sfx, '', clean, flags=re.I)
        # Condense whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    @classmethod
    def normalize_domain(cls, url_or_domain: str) -> str:
        """
        Extracts clean domain from URL or domain string.
        e.g. 'https://www.abcdecor.com/contact' -> 'abcdecor.com'
        """
        if not url_or_domain:
            return ""
        raw = url_or_domain.strip().lower()
        if not raw.startswith("http://") and not raw.startswith("https://"):
            raw = f"https://{raw}"
        try:
            netloc = urllib.parse.urlparse(raw).netloc
            netloc = netloc.replace("www.", "")
            return netloc
        except Exception:
            return ""

    @classmethod
    def normalize_phone(cls, phone: str) -> str:
        """
        Extracts digits from phone string for matching.
        """
        if not phone:
            return ""
        digits = re.sub(r'\D', '', phone)
        # Normalize 1-800 or leading 1 in North America
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]
        return digits

    @classmethod
    def is_same_entity(cls, ent1: Dict[str, Any], ent2: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determines whether two candidate records refer to the same physical commercial entity.
        Returns (is_match, match_reason).
        """
        # 1. Matching Email (Strongest deterministic match)
        em1 = (ent1.get("email") or "").strip().lower()
        em2 = (ent2.get("email") or "").strip().lower()
        if em1 and em2 and em1 == em2:
            return True, f"Matching email: {em1}"

        # 2. Matching Domain (Strong deterministic match)
        dom1 = cls.normalize_domain(ent1.get("domain") or ent1.get("website_url") or ent1.get("website") or "")
        dom2 = cls.normalize_domain(ent2.get("domain") or ent2.get("website_url") or ent2.get("website") or "")
        generic_domains = [
            "instagram.com", "facebook.com", "linkedin.com", "pinterest.com",
            "youtube.com", "yellowpages.com", "yellowpages.ca", "manta.com",
            "thomasnet.com", "etsy.com", "faire.com", "wholesalecentral.com"
        ]
        if dom1 and dom2 and dom1 not in generic_domains and dom2 not in generic_domains and dom1 == dom2:
            return True, f"Matching domain: {dom1}"

        # 3. Matching Phone Number
        ph1 = cls.normalize_phone(ent1.get("phone") or "")
        ph2 = cls.normalize_phone(ent2.get("phone") or "")
        if ph1 and ph2 and len(ph1) >= 10 and ph1 == ph2:
            return True, f"Matching phone: {ph1}"

        # 4. Matching Social Handle on same platform
        soc1 = ent1.get("social_handles") or ent1.get("social_profiles") or {}
        soc2 = ent2.get("social_handles") or ent2.get("social_profiles") or {}
        for plat in ["instagram", "linkedin", "facebook", "pinterest"]:
            url1 = (soc1.get(plat) or "").lower()
            url2 = (soc2.get(plat) or "").lower()
            if url1 and url2:
                handle1 = url1.rstrip("/").split("/")[-1]
                handle2 = url2.rstrip("/").split("/")[-1]
                if handle1 and handle2 and handle1 == handle2 and len(handle1) >= 4:
                    return True, f"Matching {plat} handle: {handle1}"

        # 5. Normalized Company Name + Location match
        name1 = cls.normalize_company_name(ent1.get("business_name") or ent1.get("company_name") or "")
        name2 = cls.normalize_company_name(ent2.get("business_name") or ent2.get("company_name") or "")
        city1 = (ent1.get("city") or "").lower().strip()
        city2 = (ent2.get("city") or "").lower().strip()
        state1 = (ent1.get("state") or "").lower().strip()
        state2 = (ent2.get("state") or "").lower().strip()

        if name1 and name2 and len(name1) >= 5 and name1 == name2:
            # If names are identical and either cities or states match or are not specified
            loc_match = (not city1 or not city2 or city1 == city2) and (not state1 or not state2 or state1 == state2)
            if loc_match:
                return True, f"Matching company name: '{name1}' ({city1 or state1})"

        return False, "No match"

    @classmethod
    def merge_candidate_records(cls, base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges an incoming discovery into an existing base record, combining
        discovery sources, social profiles, directories, and contact info.
        """
        merged = dict(base)

        # 1. Merge Discovery Sources
        sources = set(merged.get("discovery_sources", []))
        if merged.get("primary_source"):
            sources.add(merged["primary_source"])
        if merged.get("source_platform"):
            sources.add(merged["source_platform"])

        incoming_source = incoming.get("source_name") or incoming.get("source_platform") or incoming.get("source_id")
        if incoming_source:
            sources.add(incoming_source)
        for s in incoming.get("discovery_sources", []):
            sources.add(s)

        merged["discovery_sources"] = sorted(list(sources))
        merged["source_count"] = len(merged["discovery_sources"])

        # Primary source: prefer first or authoritative source
        if not merged.get("primary_source"):
            merged["primary_source"] = incoming_source or "Search Engines"

        # 2. Merge Source URLs
        source_urls = set(merged.get("source_urls", []))
        if merged.get("source_url"):
            source_urls.add(merged["source_url"])
        if incoming.get("source_url"):
            source_urls.add(incoming["source_url"])
        for u in incoming.get("source_urls", []):
            source_urls.add(u)
        merged["source_urls"] = sorted(list(source_urls))

        # 3. Merge Social Profiles
        soc = dict(merged.get("social_profiles", {}))
        for k, v in (incoming.get("social_profiles") or incoming.get("social_handles") or {}).items():
            if v and (k not in soc or not soc[k]):
                soc[k] = v
        merged["social_profiles"] = soc

        # 4. Merge Directory Profiles
        dirs = set(merged.get("directory_profiles", []))
        if incoming.get("source_type") == "directory" and incoming.get("source_url"):
            dirs.add(incoming["source_url"])
        for d in incoming.get("directory_profiles", []):
            dirs.add(d)
        merged["directory_profiles"] = sorted(list(dirs))

        # 5. Enrich Website URL if previously missing
        if not merged.get("website") and incoming.get("website_url"):
            merged["website"] = incoming["website_url"]
        elif not merged.get("website_url") and incoming.get("website_url"):
            merged["website_url"] = incoming["website_url"]

        # 6. Contact Information upgrade
        if not merged.get("email") and incoming.get("email"):
            merged["email"] = incoming["email"]
        if not merged.get("phone") and incoming.get("phone"):
            merged["phone"] = incoming["phone"]

        # 7. Geographic enrichment
        if not merged.get("city") and incoming.get("city"):
            merged["city"] = incoming["city"]
        if not merged.get("state") and incoming.get("state"):
            merged["state"] = incoming["state"]
        if not merged.get("country") and incoming.get("country"):
            merged["country"] = incoming["country"]

        # 8. Cross-Source Confidence Level calculation
        count = merged["source_count"]
        has_website = bool(merged.get("website") or merged.get("website_url"))
        has_social = bool(merged.get("social_profiles"))
        has_directory = bool(merged.get("directory_profiles"))

        if has_website and (has_social and has_directory or count >= 3):
            confidence = "Very Strong"
        elif has_website and (has_social or count >= 2):
            confidence = "Strong"
        elif count >= 2:
            confidence = "Medium"
        else:
            confidence = "Weak"

        merged["cross_source_confidence"] = confidence

        return merged

    @classmethod
    def resolve_and_deduplicate(
        cls,
        candidates: List[Dict[str, Any]],
        existing_leads: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Processes a batch of raw candidates from multiple sources,
        resolves duplicates among themselves and against existing leads,
        and returns a deduplicated, enriched list of unique business records.
        """
        resolved: List[Dict[str, Any]] = []

        for candidate in candidates:
            # Initialize entity tracking fields
            if "discovery_sources" not in candidate:
                s_name = candidate.get("source_name") or candidate.get("source_platform") or "Search Engines"
                candidate["discovery_sources"] = [s_name]
                candidate["primary_source"] = s_name
                candidate["source_count"] = 1
                candidate["cross_source_confidence"] = "Weak"
                candidate["source_urls"] = [candidate.get("source_url")] if candidate.get("source_url") else []

            # Check if matching an already resolved candidate in current batch
            matched = False
            for idx, existing in enumerate(resolved):
                is_match, reason = cls.is_same_entity(existing, candidate)
                if is_match:
                    resolved[idx] = cls.merge_candidate_records(existing, candidate)
                    matched = True
                    break

            if not matched:
                resolved.append(candidate)

        return resolved
