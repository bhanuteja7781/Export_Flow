"""
search_module.py - Supercharged Multi-Platform Buyer Discovery Engine (America & Canada)
Finds brand-new buyers on every search across:
- Granular State & City Search Crawling (30+ US States, 7 Canadian Provinces, 80+ Cities)
- High-Conversion Diaspora & Indian Handicrafts / Ethnic Decor Sourcing (Little India hubs, pooja/mandir, brassware)
- Wholesalers, Bulk Importers & Cash-and-Carry Distributors
- Furniture & Home Furnishings Showrooms
- Home Décor Retailers & Independent Lifestyle Boutiques
- Multi-Platform Dorks: Google/Bing Web, LinkedIn, Instagram, Facebook, B2B Trade Directories
- 250+ Verified North American Wholesale, Diaspora & Retail Buyer Registry
"""

import os
import re
import json
import random
import urllib.parse
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

from .discovery import MultiSourceDiscoveryEngine
from .discovery.location_registry import resolve_geographic_location


class BuyerSearchModule:
    """
    Continuous Multi-Platform Real Buyer Discovery Engine across States & Cities in America & Canada.
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
    ]

    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    
    EXCLUDE_EMAIL_PATTERNS = [
        'sentry.io', 'wixpress.com', 'schema.org', 'domain.com', 'example.com',
        'yourname@', 'email@email.com', 'name@domain.com', 'user@domain.com',
        'bootstrap', 'cloudflare', 'github.com', 'google.com', 'w3.org', 'wordpress.com'
    ]

    # Comprehensive North American Geographic Matrix (States, Provinces, Key Cities & Diaspora Hubs)
    GEOGRAPHIC_REGIONS = [
        # --- Canadian Provinces & Major Metro/Diaspora Hubs ---
        {"country": "Canada", "state": "Ontario", "city": "Toronto", "is_diaspora_hub": True},
        {"country": "Canada", "state": "Ontario", "city": "Brampton", "is_diaspora_hub": True},
        {"country": "Canada", "state": "Ontario", "city": "Mississauga", "is_diaspora_hub": True},
        {"country": "Canada", "state": "Ontario", "city": "Markham", "is_diaspora_hub": True},
        {"country": "Canada", "state": "Ontario", "city": "Ottawa", "is_diaspora_hub": False},
        {"country": "Canada", "state": "Ontario", "city": "Hamilton", "is_diaspora_hub": False},
        {"country": "Canada", "state": "Ontario", "city": "London", "is_diaspora_hub": False},
        {"country": "Canada", "state": "British Columbia", "city": "Vancouver", "is_diaspora_hub": True},
        {"country": "Canada", "state": "British Columbia", "city": "Surrey", "is_diaspora_hub": True},
        {"country": "Canada", "state": "British Columbia", "city": "Richmond", "is_diaspora_hub": True},
        {"country": "Canada", "state": "British Columbia", "city": "Victoria", "is_diaspora_hub": False},
        {"country": "Canada", "state": "British Columbia", "city": "Kelowna", "is_diaspora_hub": False},
        {"country": "Canada", "state": "Quebec", "city": "Montreal", "is_diaspora_hub": True},
        {"country": "Canada", "state": "Quebec", "city": "Quebec City", "is_diaspora_hub": False},
        {"country": "Canada", "state": "Quebec", "city": "Laval", "is_diaspora_hub": False},
        {"country": "Canada", "state": "Alberta", "city": "Calgary", "is_diaspora_hub": True},
        {"country": "Canada", "state": "Alberta", "city": "Edmonton", "is_diaspora_hub": True},
        {"country": "Canada", "state": "Manitoba", "city": "Winnipeg", "is_diaspora_hub": False},
        {"country": "Canada", "state": "Saskatchewan", "city": "Saskatoon", "is_diaspora_hub": False},
        {"country": "Canada", "state": "Nova Scotia", "city": "Halifax", "is_diaspora_hub": False},

        # --- US States & Key Cities / Diaspora Centers ---
        {"country": "United States", "state": "New Jersey", "city": "Edison", "is_diaspora_hub": True},
        {"country": "United States", "state": "New Jersey", "city": "Iselin", "is_diaspora_hub": True},
        {"country": "United States", "state": "New Jersey", "city": "Jersey City", "is_diaspora_hub": True},
        {"country": "United States", "state": "New Jersey", "city": "Woodbridge", "is_diaspora_hub": True},
        {"country": "United States", "state": "New Jersey", "city": "Parsippany", "is_diaspora_hub": True},
        {"country": "United States", "state": "New York", "city": "New York", "is_diaspora_hub": True},
        {"country": "United States", "state": "New York", "city": "Queens", "is_diaspora_hub": True},
        {"country": "United States", "state": "New York", "city": "Brooklyn", "is_diaspora_hub": True},
        {"country": "United States", "state": "New York", "city": "Long Island", "is_diaspora_hub": False},
        {"country": "United States", "state": "New York", "city": "Buffalo", "is_diaspora_hub": False},
        {"country": "United States", "state": "California", "city": "Los Angeles", "is_diaspora_hub": True},
        {"country": "United States", "state": "California", "city": "Artesia", "is_diaspora_hub": True},
        {"country": "United States", "state": "California", "city": "Fremont", "is_diaspora_hub": True},
        {"country": "United States", "state": "California", "city": "San Jose", "is_diaspora_hub": True},
        {"country": "United States", "state": "California", "city": "San Francisco", "is_diaspora_hub": True},
        {"country": "United States", "state": "California", "city": "San Diego", "is_diaspora_hub": False},
        {"country": "United States", "state": "California", "city": "Sacramento", "is_diaspora_hub": False},
        {"country": "United States", "state": "Texas", "city": "Houston", "is_diaspora_hub": True},
        {"country": "United States", "state": "Texas", "city": "Dallas", "is_diaspora_hub": True},
        {"country": "United States", "state": "Texas", "city": "Irving", "is_diaspora_hub": True},
        {"country": "United States", "state": "Texas", "city": "Sugar Land", "is_diaspora_hub": True},
        {"country": "United States", "state": "Texas", "city": "Plano", "is_diaspora_hub": True},
        {"country": "United States", "state": "Texas", "city": "Austin", "is_diaspora_hub": False},
        {"country": "United States", "state": "Texas", "city": "San Antonio", "is_diaspora_hub": False},
        {"country": "United States", "state": "Illinois", "city": "Chicago", "is_diaspora_hub": True},
        {"country": "United States", "state": "Illinois", "city": "Naperville", "is_diaspora_hub": True},
        {"country": "United States", "state": "Illinois", "city": "Schaumburg", "is_diaspora_hub": True},
        {"country": "United States", "state": "Georgia", "city": "Atlanta", "is_diaspora_hub": True},
        {"country": "United States", "state": "Georgia", "city": "Alpharetta", "is_diaspora_hub": True},
        {"country": "United States", "state": "Georgia", "city": "Duluth", "is_diaspora_hub": True},
        {"country": "United States", "state": "Washington", "city": "Seattle", "is_diaspora_hub": True},
        {"country": "United States", "state": "Washington", "city": "Bellevue", "is_diaspora_hub": True},
        {"country": "United States", "state": "North Carolina", "city": "Charlotte", "is_diaspora_hub": True},
        {"country": "United States", "state": "North Carolina", "city": "Raleigh", "is_diaspora_hub": True},
        {"country": "United States", "state": "North Carolina", "city": "Cary", "is_diaspora_hub": True},
        {"country": "United States", "state": "Florida", "city": "Miami", "is_diaspora_hub": False},
        {"country": "United States", "state": "Florida", "city": "Orlando", "is_diaspora_hub": True},
        {"country": "United States", "state": "Florida", "city": "Tampa", "is_diaspora_hub": True},
        {"country": "United States", "state": "Ohio", "city": "Columbus", "is_diaspora_hub": True},
        {"country": "United States", "state": "Ohio", "city": "Cleveland", "is_diaspora_hub": False},
        {"country": "United States", "state": "Ohio", "city": "Cincinnati", "is_diaspora_hub": False},
        {"country": "United States", "state": "Pennsylvania", "city": "Philadelphia", "is_diaspora_hub": True},
        {"country": "United States", "state": "Pennsylvania", "city": "Upper Darby", "is_diaspora_hub": True},
        {"country": "United States", "state": "Pennsylvania", "city": "Pittsburgh", "is_diaspora_hub": False},
        {"country": "United States", "state": "Virginia", "city": "Herndon", "is_diaspora_hub": True},
        {"country": "United States", "state": "Virginia", "city": "Sterling", "is_diaspora_hub": True},
        {"country": "United States", "state": "Virginia", "city": "Richmond", "is_diaspora_hub": False},
        {"country": "United States", "state": "Massachusetts", "city": "Boston", "is_diaspora_hub": True},
        {"country": "United States", "state": "Massachusetts", "city": "Cambridge", "is_diaspora_hub": False},
        {"country": "United States", "state": "Michigan", "city": "Detroit", "is_diaspora_hub": True},
        {"country": "United States", "state": "Michigan", "city": "Troy", "is_diaspora_hub": True},
        {"country": "United States", "state": "Michigan", "city": "Farmington Hills", "is_diaspora_hub": True},
        {"country": "United States", "state": "Arizona", "city": "Phoenix", "is_diaspora_hub": False},
        {"country": "United States", "state": "Arizona", "city": "Scottsdale", "is_diaspora_hub": False},
        {"country": "United States", "state": "Arizona", "city": "Chandler", "is_diaspora_hub": True},
        {"country": "United States", "state": "Colorado", "city": "Denver", "is_diaspora_hub": False},
        {"country": "United States", "state": "Maryland", "city": "Rockville", "is_diaspora_hub": True},
        {"country": "United States", "state": "Maryland", "city": "Silver Spring", "is_diaspora_hub": True},
        {"country": "United States", "state": "Maryland", "city": "Baltimore", "is_diaspora_hub": False},
        {"country": "United States", "state": "Minnesota", "city": "Minneapolis", "is_diaspora_hub": False},
        {"country": "United States", "state": "Tennessee", "city": "Nashville", "is_diaspora_hub": False},
        {"country": "United States", "state": "Missouri", "city": "St. Louis", "is_diaspora_hub": False},
        {"country": "United States", "state": "Indiana", "city": "Indianapolis", "is_diaspora_hub": False},
        {"country": "United States", "state": "Oregon", "city": "Portland", "is_diaspora_hub": False},
        {"country": "United States", "state": "Nevada", "city": "Las Vegas", "is_diaspora_hub": False}
    ]

    BUYER_TYPE_MAP = {
        "diaspora_ethnic": "Diaspora & Ethnic Decor / Indian Handicrafts",
        "wholesale_distributor": "Wholesale Distributor & Importer",
        "home_decor_retailer": "Home Décor Retailer",
        "furniture_lifestyle": "Furniture & Home Furnishings",
        "gift_specialty": "Gift & Specialty Boutique",
        "interior_design": "Interior Design Studio",
        "hospitality_events": "Hotels & Event Stylists"
    }

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.state_file = os.path.join(self.data_dir, "search_state.json")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        })
        self._load_state()
        self.discovery_engine = MultiSourceDiscoveryEngine(self.data_dir)

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception:
                self.state = {"iteration": 0, "offset": 0, "region_idx": 0, "platform_idx": 0}
        else:
            self.state = {"iteration": 0, "offset": 0, "region_idx": 0, "platform_idx": 0}

    def _save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception:
            pass

    def reset_state(self):
        self.state = {"iteration": 0, "offset": 0, "region_idx": 0, "platform_idx": 0}
        self._save_state()

    def get_available_sources(self) -> List[Dict[str, Any]]:
        return self.discovery_engine.get_available_sources()

    def get_discovery_modes(self) -> List[Dict[str, Any]]:
        return self.discovery_engine.get_discovery_modes()

    def get_source_analytics(self, leads: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        return self.discovery_engine.analytics_manager.get_source_analytics(leads)

    def _load_auto_exclusions(self) -> Tuple[Set[str], Set[str]]:
        excluded_emails = set()
        excluded_domains = set()

        del_path = os.path.join(self.data_dir, "deleted_leads.json")
        if os.path.exists(del_path):
            try:
                with open(del_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for em in data.get("emails", []):
                        if em:
                            excluded_emails.add(str(em).strip().lower())
            except Exception:
                pass

        leads_path = os.path.join(self.data_dir, "leads.json")
        if os.path.exists(leads_path):
            try:
                with open(leads_path, "r", encoding="utf-8") as f:
                    leads_data = json.load(f)
                    for l in leads_data:
                        em = (l.get("email") or "").strip().lower()
                        if em:
                            excluded_emails.add(em)
            except Exception:
                pass

        sent_path = os.path.join(self.data_dir, "sent_log.csv")
        if os.path.exists(sent_path):
            try:
                import csv
                with open(sent_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        em = (r.get("EMAIL ADDRESS") or "").strip().lower()
                        if em:
                            excluded_emails.add(em)
            except Exception:
                pass

        return excluded_emails, excluded_domains

    DISQUALIFIED_EMAIL_PREFIXES = [
        'customerservice', 'customercare', 'custserv', 'service', 'services',
        'support', 'help', 'helpdesk', 'care', 'cs', 'clientservices', 'consumer',
        'returns', 'shipping', 'billing', 'accounting', 'invoice', 'accounts',
        'jobs', 'careers', 'recruiting', 'media', 'press', 'privacy', 'legal',
        'unsubscribe', 'newsletter', 'noreply', 'no-reply', 'marketing', 'guestservices',
        'reservations'
    ]

    def _is_customer_service_email(self, email: str) -> bool:
        if not email or '@' not in email:
            return True
        prefix = email.split('@')[0].lower().replace('.', '').replace('-', '').replace('_', '')
        for disq in self.DISQUALIFIED_EMAIL_PREFIXES:
            disq_clean = disq.replace('.', '').replace('-', '').replace('_', '')
            if prefix == disq_clean or prefix.startswith(disq_clean):
                return True
        return False

    def _is_lead_excluded(self, lead: Dict[str, Any], exclude_emails: Set[str], exclude_domains: Set[str]) -> bool:
        lead_em = (lead.get("email") or "").strip().lower()
        if lead_em and (lead_em in exclude_emails or self._is_customer_service_email(lead_em)):
            return True

        content = lead.get("raw_content", "") or lead.get("title", "")
        for em in self.EMAIL_REGEX.findall(content):
            clean_em = em.strip().lower()
            if clean_em in exclude_emails or self._is_customer_service_email(clean_em):
                return True

        return False

    def search(
        self,
        keyword: str = "Metal Candle Holders",
        sources: Optional[List[str]] = None,
        max_results: int = 10,
        discovery_mode: str = "all",
        country: Optional[str] = "America & Canada",
        state: Optional[str] = None,
        city: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        buyer_size: Optional[str] = "all",
        price_segment: Optional[str] = "all",
        diaspora_focus: bool = False,
        target_domains: Optional[List[str]] = None,
        exclude_emails: Optional[Set[str]] = None,
        exclude_domains: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes autonomous multi-source buyer discovery across search engines, social media,
        business directories, wholesale ecosystems, and direct website crawlers.
        """
        self.state["iteration"] = self.state.get("iteration", 0) + 1
        self.state["offset"] = (self.state.get("offset", 0) + 12) % 300
        self.state["region_idx"] = (self.state.get("region_idx", 0) + 4) % len(self.GEOGRAPHIC_REGIONS)
        self.state["platform_idx"] = (self.state.get("platform_idx", 0) + 1) % 4
        self._save_state()

        auto_excluded_emails, auto_excluded_domains = self._load_auto_exclusions()
        exclude_emails = {e.strip().lower() for e in (exclude_emails or set()) if e} | auto_excluded_emails
        exclude_domains = {d.strip().lower() for d in (exclude_domains or set()) if d} | auto_excluded_domains

        # Map discovery_mode to standard engine mode
        mode_map = {
            "all": "multi_source",
            "quick": "quick_crawl",
            "quick_crawl": "quick_crawl",
            "deep": "deep_crawl",
            "deep_crawl": "deep_crawl",
            "social": "social_discovery",
            "social_discovery": "social_discovery",
            "wholesale": "wholesale_discovery",
            "wholesale_discovery": "wholesale_discovery",
            "retail": "retail_discovery",
            "retail_discovery": "retail_discovery",
            "multi_source": "multi_source"
        }
        engine_mode = mode_map.get((discovery_mode or "all").lower(), "multi_source")

        # 1. Primary Multi-Source Live Web Discovery Engine execution
        discovered_leads = self.discovery_engine.discover_buyers(
            keyword=keyword,
            discovery_mode=engine_mode,
            enabled_sources=sources,
            country=country if country != "All" else "America & Canada",
            state=state if state != "all" else None,
            city=city if city != "all" else None,
            buyer_type=buyer_type,
            buyer_size=buyer_size,
            price_segment=price_segment,
            diaspora_focus=diaspora_focus or (buyer_type == "diaspora_ethnic"),
            target_domains=target_domains,
            max_results=max_results,
            offset=self.state.get("offset", 0),
            exclude_emails=exclude_emails,
            exclude_domains=exclude_domains
        )

        # 2. If fewer than max_results discovered, execute a fast secondary live web discovery pass
        if len(discovered_leads) < max_results:
            seen_emails = {l.get("email", "").lower() for l in discovered_leads if l.get("email")} | exclude_emails
            seen_domains = {self._extract_domain(l.get("website", "") or l.get("url", "")) for l in discovered_leads} | exclude_domains
            
            comp_kw = f"{keyword} boutique store gifts"
            extra_cands = self.discovery_engine.discover_buyers(
                keyword=comp_kw,
                discovery_mode=engine_mode,
                enabled_sources=["search_engine", "wholesale", "directory"],
                country=country if country != "All" else "America & Canada",
                state=state if state != "all" else None,
                city=city if city != "all" else None,
                buyer_type=buyer_type,
                buyer_size=buyer_size,
                price_segment=price_segment,
                diaspora_focus=diaspora_focus or (buyer_type == "diaspora_ethnic"),
                max_results=max_results - len(discovered_leads),
                offset=self.state.get("offset", 0) + 15,
                exclude_emails=seen_emails,
                exclude_domains=seen_domains
            )
            for cand in extra_cands:
                em = (cand.get("email") or "").lower().strip()
                dom = self._extract_domain(cand.get("website", "") or cand.get("url", ""))
                if em and em not in seen_emails and dom not in seen_domains:
                    seen_emails.add(em)
                    seen_domains.add(dom)
                    discovered_leads.append(cand)
                    if len(discovered_leads) >= max_results:
                        break

        return discovered_leads[:max_results]

    def _get_active_geographic_clause(self, country: Optional[str], state: Optional[str] = None, city: Optional[str] = None, diaspora_only: bool = False) -> Tuple[str, str, str, str]:
        """
        Builds localized search clauses drilling into specific States, Provinces, Cities and Diaspora Hubs.
        """
        req_country = (country or "").lower().strip()
        filtered_regions = self.GEOGRAPHIC_REGIONS

        if "canada" in req_country and ("america" not in req_country and "all" not in req_country and "usa" not in req_country):
            filtered_regions = [r for r in filtered_regions if str(r.get("country", "")) == "Canada"]
        elif "united states" in req_country or "usa" in req_country or req_country == "us":
            if "canada" not in req_country and "america" not in req_country and "all" not in req_country:
                filtered_regions = [r for r in filtered_regions if str(r.get("country", "")) == "United States"]

        if state and state != "all":
            state_lower = state.lower()
            filtered_regions = [r for r in filtered_regions if state_lower in str(r.get("state", "")).lower()] or filtered_regions

        if city and city != "all":
            city_lower = city.lower()
            filtered_regions = [r for r in filtered_regions if city_lower in str(r.get("city", "")).lower()] or filtered_regions

        if diaspora_only:
            diaspora_matches = [r for r in filtered_regions if bool(r.get("is_diaspora_hub"))]
            if diaspora_matches:
                filtered_regions = diaspora_matches

        reg_idx = self.state.get("region_idx", 0) % max(1, len(filtered_regions))
        selected_region = filtered_regions[reg_idx]

        target_city: str = str(selected_region.get("city", ""))
        target_state: str = str(selected_region.get("state", ""))
        target_country: str = str(selected_region.get("country", "United States"))

        loc_clause = f'("{target_city}" OR "{target_state}")'
        return loc_clause, target_city, target_state, target_country

    def _matches_country(self, lead: Dict[str, Any], requested_country: Optional[str]) -> bool:
        if not lead:
            return False

        lead_country = lead.get("country", "")
        lead_content = (lead.get("raw_content", "") + " " + lead.get("title", "") + " " + lead.get("source_platform", "")).lower()
        url = lead.get("url", "").lower()

        is_canada = (
            lead_country == "Canada" or
            url.endswith(".ca") or
            ".ca/" in url or
            any(kw in lead_content for kw in [
                "canada", "toronto", "brampton", "mississauga", "vancouver", "surrey", "montreal", "quebec", "ontario",
                "calgary", "ottawa", "alberta", "british columbia", "edmonton", "winnipeg",
                "halifax", "nova scotia", "victoria bc", "saskatchewan", "markham"
            ])
        )

        is_usa = (
            lead_country == "United States" or
            url.endswith(".us") or
            any(kw in lead_content for kw in [
                "united states", "usa", "u.s.a", "california", "new york", "texas", "new jersey", "edison", "iselin",
                "florida", "illinois", "chicago", "los angeles", "georgia", "colorado", "artesia", "fremont", "irving",
                "massachusetts", "north carolina", "ohio", "washington", "seattle",
                "atlanta", "dallas", "houston", "miami", "boston", "phoenix", "denver", "sugar land"
            ])
        )

        if is_canada and not is_usa:
            lead["country"] = "Canada"
        elif is_usa and not is_canada:
            lead["country"] = "United States"
        elif is_canada:
            lead["country"] = "Canada"
        else:
            lead["country"] = "United States"

        req = (requested_country or "").lower().strip()
        if "canada" in req and ("america" not in req and "all" not in req and "usa" not in req and "united" not in req):
            return lead["country"] == "Canada"
        elif "united states" in req or "usa" in req or req == "us":
            if "canada" not in req and "america" not in req and "all" not in req:
                return lead["country"] == "United States"

        return lead["country"] in ["Canada", "United States"]

    def _extract_domain(self, url: str) -> str:
        try:
            return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
        except Exception:
            return ""

    # -------------------------------------------------------------
    # 1. Multi-Engine Web Discovery (State, City & Diaspora Dorks)
    # -------------------------------------------------------------
    def _discover_via_multi_engine_web(
        self,
        keyword: str,
        country: Optional[str],
        state: Optional[str] = None,
        city: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        buyer_size: Optional[str] = "all",
        price_segment: Optional[str] = "all",
        diaspora_focus: bool = False,
        offset: int = 0,
        max_leads: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Discovers authentic live domains via Google/Bing/DDG queries across State & City Wholesalers, Retailers, Furniture Stores and Diaspora.
        """
        loc_clause, target_city, target_state, target_country = self._get_active_geographic_clause(country, state, city, diaspora_focus)

        queries = []

        # A. Diaspora & Indian Handicrafts / Ethnic Decor Queries
        if diaspora_focus or buyer_type == "diaspora_ethnic":
            queries.extend([
                f'"{keyword}" ("Indian home decor" OR "Indian handicrafts" OR "brass pooja" OR "mandir decor" OR "Diwali decor" OR "ethnic home") {loc_clause}',
                f'("Indian gift shop" OR "South Asian home decor" OR "handicraft store" OR "Indian brassware" OR "ethnic lifestyle store") ("contact" OR "wholesale" OR "shop") {loc_clause}',
                f'("Indian store" OR "pooja items store" OR "ethnic decor boutique") "{keyword}" {loc_clause}'
            ])
        # B. Wholesalers, Importers & Cash-and-Carry
        elif buyer_type == "wholesale_distributor" or buyer_size == "enterprise_large":
            queries.extend([
                f'"{keyword}" ("wholesale distributor" OR "cash and carry" OR "home decor importer" OR "direct importer" OR "b2b warehouse") ("contact" OR "wholesale") {loc_clause}',
                f'("home decor wholesale" OR "giftware distributor" OR "metalware importer") "{keyword}" {loc_clause}'
            ])
        # C. Furniture & Home Furnishings
        elif buyer_type == "furniture_lifestyle":
            queries.extend([
                f'"{keyword}" ("furniture store" OR "home furnishings" OR "furniture showroom" OR "accent furniture" OR "tabletop accessories") {loc_clause}',
                f'("furniture outlet" OR "home lifestyle showroom" OR "tabletop decor") "{keyword}" ("contact" OR "shop") {loc_clause}'
            ])
        # D. Home Décor & Independent Retailers (Default)
        else:
            queries.extend([
                f'"{keyword}" ("home decor store" OR "gift shop" OR "lifestyle boutique" OR "candle store" OR "decor stockist") {loc_clause}',
                f'"{keyword}" ("wholesale" OR "distributor" OR "retail store" OR "Indian home decor") ("contact" OR "email") {loc_clause}',
                f'"{keyword}" ("furniture store" OR "home accents" OR "tabletop decor" OR "independent shop") {loc_clause}'
            ])

        discovered_urls: List[str] = []
        for q in queries:
            if len(discovered_urls) >= max_leads * 2:
                break
            urls = self._query_bing_and_ddg(q, offset=offset, max_items=4)
            discovered_urls.extend(urls)

        results = []
        with ThreadPoolExecutor(max_workers=min(4, max(1, len(discovered_urls)))) as executor:
            future_to_url = {executor.submit(self._crawl_single_website, url, target_country): url for url in discovered_urls[:max_leads * 2]}
            for future in as_completed(future_to_url):
                try:
                    lead = future.result()
                    if lead:
                        lead["state"] = target_state
                        lead["city"] = target_city
                        lead["country"] = target_country
                        lead["category"] = buyer_type if buyer_type != "all" else ("diaspora_ethnic" if diaspora_focus else "home_decor_retailer")
                        lead["buyer_size"] = buyer_size if buyer_size != "all" else "independent_small"
                        lead["market_segment"] = "diaspora" if diaspora_focus else ("mid_range" if price_segment != "high_end" else "high_end")
                        lead["source_platform"] = f"Web Crawler ({target_city}, {target_state})"
                        results.append(lead)
                        if len(results) >= max_leads:
                            break
                except Exception:
                    pass

        return results

    # -------------------------------------------------------------
    # 2. LinkedIn Sourcing (Purchasing Directors, Merchandisers & Owners)
    # -------------------------------------------------------------
    def _discover_via_linkedin(
        self,
        keyword: str,
        country: Optional[str],
        state: Optional[str] = None,
        city: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        buyer_size: Optional[str] = "all",
        price_segment: Optional[str] = "all",
        diaspora_focus: bool = False,
        offset: int = 0,
        max_leads: int = 4
    ) -> List[Dict[str, Any]]:
        loc_clause, target_city, target_state, target_country = self._get_active_geographic_clause(country, state, city, diaspora_focus)

        if diaspora_focus or buyer_type == "diaspora_ethnic":
            queries = [
                f'site:linkedin.com/company ("Indian home decor" OR "Indian handicrafts" OR "ethnic decor" OR "pooja items") {loc_clause}',
                f'site:linkedin.com/in ("founder" OR "owner" OR "buyer") ("Indian decor" OR "handicrafts" OR "ethnic goods") {loc_clause}'
            ]
        elif buyer_type == "wholesale_distributor":
            queries = [
                f'site:linkedin.com/company "{keyword}" ("wholesale distributor" OR "importer" OR "b2b home goods") {loc_clause}',
                f'site:linkedin.com/in ("purchasing manager" OR "category buyer" OR "sourcing director") "{keyword}" {loc_clause}'
            ]
        elif buyer_type == "furniture_lifestyle":
            queries = [
                f'site:linkedin.com/company ("furniture store" OR "home furnishings" OR "furniture gallery") "{keyword}" {loc_clause}',
                f'site:linkedin.com/in ("furniture buyer" OR "merchandiser" OR "showroom manager") "{keyword}" {loc_clause}'
            ]
        else:
            queries = [
                f'site:linkedin.com/company "{keyword}" ("home decor" OR "retail store" OR "gift shop") {loc_clause}',
                f'site:linkedin.com/in ("buyer" OR "owner" OR "merchandising") "{keyword}" {loc_clause}'
            ]

        snippets = []
        for q in queries:
            if len(snippets) >= max_leads:
                break
            res = self._query_ddg_snippets(q, offset=offset, max_items=4)
            snippets.extend(res)

        results = []
        for s in snippets:
            title_clean = re.split(r'\s+[-–|—]\s+|\s*:\s*', s["title"][:50])[0].strip() or "Commercial Buyer"
            cat = buyer_type if buyer_type != "all" else ("diaspora_ethnic" if diaspora_focus else "wholesale_distributor")
            results.append({
                "category": cat,
                "buyer_size": buyer_size if buyer_size != "all" else "mid_market",
                "market_segment": "diaspora" if diaspora_focus else "mid_range",
                "title": f"{title_clean} - LinkedIn Buyer",
                "raw_content": f"{title_clean}. Sourcing {keyword}. Profile: {s['text']}. Platform: LinkedIn. Location: {target_city}, {target_state}, {target_country}. Url: {s['url']}",
                "url": s["url"],
                "state": target_state,
                "city": target_city,
                "country": target_country,
                "source_platform": f"LinkedIn ({target_city}, {target_state})"
            })
            if len(results) >= max_leads:
                break

        return results

    # -------------------------------------------------------------
    # 3. Instagram Sourcing (Boutiques, Stockists, Ethnic Lifestyle)
    # -------------------------------------------------------------
    def _discover_via_instagram(
        self,
        keyword: str,
        country: Optional[str],
        state: Optional[str] = None,
        city: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        buyer_size: Optional[str] = "all",
        price_segment: Optional[str] = "all",
        diaspora_focus: bool = False,
        offset: int = 0,
        max_leads: int = 4
    ) -> List[Dict[str, Any]]:
        loc_clause, target_city, target_state, target_country = self._get_active_geographic_clause(country, state, city, diaspora_focus)

        if diaspora_focus or buyer_type == "diaspora_ethnic":
            queries = [
                f'site:instagram.com ("indianhomedecor" OR "poojadecor" OR "indianhandicrafts" OR "ethnicboutique") {loc_clause} ("shop" OR "DM" OR "email")',
                f'site:instagram.com ("diwalidecor" OR "indianweddingdecor" OR "brassdecor") {loc_clause}'
            ]
        elif buyer_type == "furniture_lifestyle":
            queries = [
                f'site:instagram.com ("furniture store" OR "home furnishings" OR "tabletop accessories") "{keyword}" {loc_clause}',
                f'site:instagram.com ("modern furniture" OR "decor showroom") {loc_clause}'
            ]
        else:
            queries = [
                f'site:instagram.com "{keyword}" ("home decor store" OR "gift shop" OR "decor stockist" OR "lifestyle shop") {loc_clause} ("shop" OR "email" OR "wholesale")',
                f'site:instagram.com ("candle store" OR "tabletop decor" OR "home accents") {loc_clause}'
            ]

        snippets = []
        for q in queries:
            if len(snippets) >= max_leads:
                break
            res = self._query_ddg_snippets(q, offset=offset, max_items=4)
            snippets.extend(res)

        results = []
        for s in snippets:
            title_clean = re.split(r'\s+[-–|—]\s+|\s*:\s*', s["title"][:50])[0].strip() or "Instagram Store"
            cat = buyer_type if buyer_type != "all" else ("diaspora_ethnic" if diaspora_focus else "home_decor_retailer")
            results.append({
                "category": cat,
                "buyer_size": "independent_small",
                "market_segment": "diaspora" if diaspora_focus else "mid_range",
                "title": f"{title_clean} - Instagram Store",
                "raw_content": f"{title_clean}. Social Boutique: {s['text']}. Platform: Instagram. Location: {target_city}, {target_state}, {target_country}. Url: {s['url']}",
                "url": s["url"],
                "state": target_state,
                "city": target_city,
                "country": target_country,
                "source_platform": f"Instagram ({target_city}, {target_state})"
            })
            if len(results) >= max_leads:
                break

        return results

    # -------------------------------------------------------------
    # 4. Facebook Sourcing (Home Decor, Wholesale Groups & Store Pages)
    # -------------------------------------------------------------
    def _discover_via_facebook(
        self,
        keyword: str,
        country: Optional[str],
        state: Optional[str] = None,
        city: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        buyer_size: Optional[str] = "all",
        price_segment: Optional[str] = "all",
        diaspora_focus: bool = False,
        offset: int = 0,
        max_leads: int = 4
    ) -> List[Dict[str, Any]]:
        loc_clause, target_city, target_state, target_country = self._get_active_geographic_clause(country, state, city, diaspora_focus)

        if diaspora_focus or buyer_type == "diaspora_ethnic":
            queries = [
                f'site:facebook.com ("Indian home decor" OR "Indian gift store" OR "pooja items" OR "handicrafts store") {loc_clause} ("contact" OR "email")',
                f'site:facebook.com ("desi home decor" OR "Indian brass handicrafts") {loc_clause}'
            ]
        elif buyer_type == "wholesale_distributor":
            queries = [
                f'site:facebook.com "{keyword}" ("wholesale distributor" OR "warehouse" OR "cash and carry") {loc_clause} ("email" OR "phone" OR "wholesale")',
                f'site:facebook.com ("home decor wholesale" OR "giftware distributor") {loc_clause}'
            ]
        else:
            queries = [
                f'site:facebook.com "{keyword}" ("home decor store" OR "furniture store" OR "gift shop") {loc_clause} "contact"',
                f'site:facebook.com ("home accents" OR "tabletop decor") {loc_clause} ("email" OR "contact")'
            ]

        snippets = []
        for q in queries:
            if len(snippets) >= max_leads:
                break
            res = self._query_ddg_snippets(q, offset=offset, max_items=4)
            snippets.extend(res)

        results = []
        for s in snippets:
            title_clean = re.split(r'\s+[-–|—]\s+|\s*:\s*', s["title"][:50])[0].strip() or "Facebook Store"
            cat = buyer_type if buyer_type != "all" else ("diaspora_ethnic" if diaspora_focus else "home_decor_retailer")
            results.append({
                "category": cat,
                "buyer_size": "independent_small",
                "market_segment": "diaspora" if diaspora_focus else "mid_range",
                "title": f"{title_clean} - Facebook Store",
                "raw_content": f"{title_clean}. Business Page: {s['text']}. Platform: Facebook. Location: {target_city}, {target_state}, {target_country}. Url: {s['url']}",
                "url": s["url"],
                "state": target_state,
                "city": target_city,
                "country": target_country,
                "source_platform": f"Facebook ({target_city}, {target_state})"
            })
            if len(results) >= max_leads:
                break

        return results

    # -------------------------------------------------------------
    # 5. B2B Directories (YellowPages Canada, ThomasNet, Manta)
    # -------------------------------------------------------------
    def _discover_via_b2b_directories(
        self,
        keyword: str,
        country: Optional[str],
        state: Optional[str] = None,
        city: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        buyer_size: Optional[str] = "all",
        price_segment: Optional[str] = "all",
        diaspora_focus: bool = False,
        offset: int = 0,
        max_leads: int = 4
    ) -> List[Dict[str, Any]]:
        loc_clause, target_city, target_state, target_country = self._get_active_geographic_clause(country, state, city, diaspora_focus)

        queries = [
            f'site:yellowpages.ca OR site:yellowpages.com "{keyword}" ("wholesale" OR "retail" OR "furniture") {loc_clause}',
            f'site:manta.com OR site:thomasnet.com ("home decor" OR "giftware" OR "furniture") distributors {loc_clause}'
        ]

        discovered_urls: List[str] = []
        for q in queries:
            if len(discovered_urls) >= max_leads * 2:
                break
            urls = self._query_bing_and_ddg(q, offset=offset, max_items=3)
            discovered_urls.extend(urls)

        results = []
        with ThreadPoolExecutor(max_workers=min(3, max(1, len(discovered_urls)))) as executor:
            future_to_url = {executor.submit(self._crawl_single_website, url, target_country): url for url in discovered_urls[:max_leads]}
            for future in as_completed(future_to_url):
                try:
                    lead = future.result()
                    if lead:
                        lead["state"] = target_state
                        lead["city"] = target_city
                        lead["country"] = target_country
                        lead["category"] = "wholesale_distributor"
                        lead["buyer_size"] = "enterprise_large" if buyer_size == "enterprise_large" else "mid_market"
                        lead["market_segment"] = "volume_wholesale"
                        lead["source_platform"] = f"B2B Directory ({target_city}, {target_state})"
                        results.append(lead)
                except Exception:
                    pass

        return results

    # -------------------------------------------------------------
    # Search Engine Query Helpers (Bing + DuckDuckGo)
    # -------------------------------------------------------------
    def _query_bing_and_ddg(self, query: str, offset: int = 0, max_items: int = 5) -> List[str]:
        urls: List[str] = []

        try:
            bing_url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}&first={offset + 1}"
            resp = self.session.get(bing_url, timeout=2.5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for li in soup.find_all("li", class_="b_algo"):
                    a_tag = li.find("a")
                    if a_tag:
                        href = a_tag.get("href")
                        if isinstance(href, str) and href.startswith("http") and self._is_valid_target_url(href):
                            urls.append(href)
                            if len(urls) >= max_items:
                                return urls
        except Exception:
            pass

        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
            if offset > 0:
                ddg_url += f"&s={offset}"
            resp = self.session.get(ddg_url, timeout=2.5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for link_tag in soup.find_all("a", class_="result__url"):
                    href_val = link_tag.get("href")
                    if isinstance(href_val, str) and href_val:
                        if "uddg=" in href_val:
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href_val).query)
                            cand = parsed.get("uddg", [])
                            if cand and cand[0].startswith("http") and self._is_valid_target_url(cand[0]):
                                urls.append(cand[0])
                        elif href_val.startswith("http") and self._is_valid_target_url(href_val):
                            urls.append(href_val)
                    if len(urls) >= max_items:
                        break
        except Exception:
            pass

        return urls

    def _query_ddg_snippets(self, query: str, offset: int = 0, max_items: int = 4) -> List[Dict[str, str]]:
        results = []
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
            if offset > 0:
                url += f"&s={offset}"
            resp = self.session.get(url, timeout=2.5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for result_div in soup.find_all("div", class_="result"):
                    title_elem = result_div.find("a", class_="result__url") or result_div.find("a", class_="result__a") or result_div.find("a", class_="result__title")
                    snippet_elem = result_div.find("a", class_="result__snippet")
                    
                    if not title_elem:
                        continue
                    
                    raw_title = result_div.get_text(separator=" ", strip=True)
                    snippet_text = snippet_elem.get_text(strip=True) if snippet_elem else raw_title
                    href_attr = title_elem.get("href")
                    
                    if not isinstance(href_attr, str) or not href_attr:
                        continue

                    actual_url = href_attr
                    if "uddg=" in href_attr:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href_attr).query)
                        cand = parsed.get("uddg", [])
                        if cand:
                            actual_url = cand[0]

                    if isinstance(actual_url, str) and actual_url.startswith("http") and self._is_valid_target_url(actual_url):
                        clean_title = re.split(r'\s+[-–|—]\s+|\s*:\s*', raw_title[:60])[0].strip() or "Buyer Profile"
                        results.append({
                            "title": clean_title,
                            "url": actual_url,
                            "text": snippet_text[:250]
                        })
                        if len(results) >= max_items:
                            break
        except Exception:
            pass
        return results

    def _crawl_target_domains(self, domains_or_urls: List[str]) -> List[Dict[str, Any]]:
        clean_urls = []
        for item in domains_or_urls:
            item = item.strip()
            if not item:
                continue
            if not item.startswith("http://") and not item.startswith("https://"):
                item = f"https://{item}"
            clean_urls.append(item)

        results = []
        with ThreadPoolExecutor(max_workers=min(4, max(1, len(clean_urls)))) as executor:
            future_to_url = {executor.submit(self._crawl_single_website, url): url for url in clean_urls}
            for future in as_completed(future_to_url):
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                except Exception:
                    pass

        return results

    def _crawl_single_website(self, base_url: str, country_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        parsed_base = urllib.parse.urlparse(base_url)
        if not parsed_base.netloc:
            return None

        root_url = f"{parsed_base.scheme}://{parsed_base.netloc}"
        found_emails: Set[str] = set()
        netloc_clean = parsed_base.netloc.replace("www.", "")
        company_name = netloc_clean.split(".")[0].replace("-", " ").title()
        page_title = company_name
        full_text_corpus = []

        is_canadian = netloc_clean.endswith(".ca") or (country_hint and "canada" in country_hint.lower())
        country = "Canada" if is_canadian else "United States"

        # Biased Crawler Queue: High-value procurement, vendor, and leadership paths first
        priority_paths = [
            # 1. Procurement & Vendor Portals
            f"{root_url}/procurement",
            f"{root_url}/vendors",
            f"{root_url}/suppliers",
            f"{root_url}/partners",
            f"{root_url}/vendor-registration",
            f"{root_url}/supplier-portal",
            # 2. Leadership & Team
            f"{root_url}/leadership",
            f"{root_url}/management",
            f"{root_url}/team",
            f"{root_url}/about-us",
            # 3. Wholesale & Tenders
            f"{root_url}/wholesale",
            f"{root_url}/trade",
            f"{root_url}/tenders",
            f"{root_url}/rfps",
            # 4. Standard Contact & Root
            f"{root_url}/contact",
            f"{root_url}/contact-us",
            root_url
        ]

        discovered_internal_links = set(priority_paths)

        for target_url in priority_paths:
            try:
                resp = self.session.get(target_url, timeout=2.5, allow_redirects=True)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                if soup.title and soup.title.string:
                    clean_title = soup.title.string.strip()
                    if clean_title and target_url == root_url:
                        page_title = clean_title

                body_text = soup.get_text(separator=" ", strip=True)
                if any(prov in body_text.lower() for prov in ["ontario", "toronto", "brampton", "mississauga", "vancouver", "surrey", "british columbia", "quebec", "montreal", "calgary", "alberta", "canada"]):
                    country = "Canada"

                # 1. Parse mailto links with surrounding anchor context
                for mailto in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
                    mailto_href = mailto.get("href")
                    if isinstance(mailto_href, str):
                        raw_email = mailto_href.replace("mailto:", "").split("?")[0].strip()
                        if self._is_clean_email(raw_email):
                            found_emails.add(raw_email.lower())
                            # Capture parent container context
                            parent_text = mailto.parent.get_text(separator=" ", strip=True) if mailto.parent else ""
                            if parent_text:
                                full_text_corpus.append(parent_text[:250])

                # 2. Parse body text for emails
                matches = self.EMAIL_REGEX.findall(body_text)
                for email in matches:
                    if self._is_clean_email(email):
                        found_emails.add(email.lower())

                full_text_corpus.append(body_text[:600])

                # If high-priority procurement or named mailboxes found, we can stop early
                has_tier1_prefix = any(
                    any(email.startswith(p) for p in ['procurement', 'sourcing', 'tenders', 'purchasing', 'buyer', 'buying'])
                    for email in found_emails
                )
                if has_tier1_prefix:
                    break

                if len(found_emails) >= 3:
                    break
            except Exception:
                continue

        if not found_emails:
            return None

        emails_str = ", ".join(list(found_emails)[:3])
        snippet = f"Company: {page_title}. Contact: {emails_str}. Website: {root_url}. Country: {country}. Details: {' '.join(full_text_corpus)[:600]}"

        return {
            "title": f"{page_title} - {country} Buyer",
            "raw_content": snippet,
            "url": root_url,
            "country": country,
            "source_platform": f"Web Crawler ({country})"
        }

    def _is_clean_email(self, email: str) -> bool:
        email = email.strip().lower()
        if not email or "@" not in email:
            return False
        if any(email.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".js", ".css", ".ico"]):
            return False
        if any(pattern in email for pattern in self.EXCLUDE_EMAIL_PATTERNS):
            return False
        parts = email.split("@")
        if len(parts) != 2 or "." not in parts[1]:
            return False
        return True

    def _is_valid_target_url(self, url: str) -> bool:
        url_lower = url.lower()
        ignored_domains = [
            "duckduckgo.com", "google.com", "bing.com", "yahoo.com", "youtube.com",
            "wikipedia.org", "amazon.com", "ebay.com", "etsy.com", "reddit.com"
        ]
        return not any(ign in url_lower for ign in ignored_domains)

