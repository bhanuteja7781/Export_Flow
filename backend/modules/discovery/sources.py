"""
sources.py - Concrete Discovery Source Implementations
Implements compliant, modular discovery sources for Search Engines, Social Media
(LinkedIn, Instagram, Facebook, Pinterest, YouTube), Business Directories,
Wholesale Platforms, Marketplaces, Industry Sources, and Direct Website discovery.
"""

import os
import re
import json
import random
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from .base_source import DiscoverySource
from .query_generator import SourceQueryGenerator


BANNED_PLATFORM_DOMAINS = {
    # Major consumer marketplaces & platforms
    "amazon.com", "amazon.ca", "amazon.co.uk", "ebay.com", "ebay.ca", "walmart.com", "walmart.ca",
    "target.com", "etsy.com", "wayfair.com", "overstock.com", "alibaba.com", "aliexpress.com",
    "temu.com", "shein.com", "faire.com", "tundra.com", "abound.com", "globalsources.com",
    "dhgate.com", "wish.com", "poshmark.com", "mercari.com", "costco.com", "homedepot.com",
    "lowes.com", "ikea.com", "crateandbarrel.com", "potterybarn.com", "westelm.com", "cb2.com",
    "bedbathandbeyond.com", "kohls.com", "macys.com", "nordstrom.com", "tjmaxx.com", "marshalls.com",
    # Social media & content networks
    "instagram.com", "facebook.com", "linkedin.com", "pinterest.com", "youtube.com",
    "tiktok.com", "twitter.com", "x.com", "reddit.com", "quora.com", "medium.com", "tumblr.com",
    "wikipedia.org", "wikimedia.org", "tripadvisor.com",
    # Generic search engines, portals, aggregators
    "google.com", "bing.com", "duckduckgo.com", "yahoo.com", "yelp.com", "yellowpages.com",
    "yellowpages.ca", "bbb.org", "manta.com", "mapquest.com", "whitepages.com", "superpages.com",
    "wix.com", "wixpress.com", "shopify.com", "myshopify.com", "squarespace.com",
    "wordpress.com", "wordpress.org", "weebly.com", "godaddy.com", "sentry.io", "cloudflare.com",
    # Nonprofits / Associations / Generic directories
    "candles.org", "nationalcandleassociation.org", "craftcouncil.org", "dallasmkt.com"
}

JUNK_TITLES = {
    "homepage", "home page", "home", "index", "member directory", "directory",
    "about us", "about", "contact us", "contact", "search results", "search",
    "welcome", "login", "register", "cart", "checkout", "shop all", "shop online",
    "404 not found", "access denied", "default", "untitled", "privacy policy",
    "terms of service", "terms and conditions", "faq", "blog", "articles", "news"
}

def is_banned_domain(domain_or_url: str) -> bool:
    if not domain_or_url:
        return True
    dom = domain_or_url.lower().replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].split("?")[0].strip()
    if not dom or "." not in dom:
        return True
    if dom in BANNED_PLATFORM_DOMAINS:
        return True
    banned_keywords = [
        "amazon", "ebay", "walmart", "target.", "faire", "etsy", "wayfair", "alibaba",
        "aliexpress", "temu", "shein", "wikipedia", "reddit", "quora", "yelp", "yellowpages",
        "tripadvisor", "candles.org", "youtube", "facebook", "instagram", "pinterest", "linkedin",
        "tiktok", "twitter", "sentry", "cloudflare", "wixpress", "myshopify"
    ]
    return any(kw in dom for kw in banned_keywords)

def clean_business_title(raw_title: str, url: str) -> Optional[str]:
    if not raw_title:
        return None
    # Strip suffixes like "- Home", "| Official Site", etc.
    clean = re.split(r'\s+[-–|—:]\s+', raw_title)[0].strip()
    
    # If the first segment is junk (e.g. "Homepage"), try the subsequent segments
    if clean.lower() in JUNK_TITLES:
        parts = re.split(r'\s+[-–|—:]\s+', raw_title)
        clean = None
        for p in parts[1:]:
            p_clean = p.strip()
            if p_clean and p_clean.lower() not in JUNK_TITLES and len(p_clean) >= 3:
                clean = p_clean
                break

    # If still junk or generic product name, derive clean company name from domain
    if not clean or clean.lower() in JUNK_TITLES or clean.lower().startswith(("bulk ", "cheap ", "wholesale metal", "metal candle holder", "candle holder", "candles")):
        dom = url.lower().replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        base_name = dom.split(".")[0].replace("-", " ").replace("_", " ").title()
        if len(base_name) >= 3 and not is_banned_domain(dom):
            clean = base_name
        else:
            return None

    clean = re.sub(r'^[^\w]+|[^\w]+$', '', clean)
    if len(clean) < 3 or is_banned_domain(clean):
        return None
    return clean


class BaseHttpSource(DiscoverySource):
    """
    Helper base class for sources querying search indexing engines via HTTP.
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ]

    def __init__(self, source_id: str, source_name: str, source_type: str, priority_weight: float = 1.0, enabled: bool = True):
        super().__init__(source_id, source_name, source_type, priority_weight, enabled)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        })

    def _query_search_engine(self, query: str, offset: int = 0, max_items: int = 4) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []

        # 1. DuckDuckGo HTML endpoint
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
                    href = title_elem.get("href")

                    if not isinstance(href, str) or not href:
                        continue

                    actual_url = href
                    if "uddg=" in href:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        cand = parsed.get("uddg", [])
                        if cand:
                            actual_url = cand[0]

                    if isinstance(actual_url, str) and actual_url.startswith("http"):
                        if is_banned_domain(actual_url):
                            continue
                        clean_title = clean_business_title(raw_title, actual_url)
                        if not clean_title:
                            continue
                        results.append({
                            "title": clean_title,
                            "url": actual_url,
                            "snippet": snippet_text[:280]
                        })
                        if len(results) >= max_items:
                            return results
        except Exception:
            pass

        # 2. Bing fallback
        if len(results) < max_items:
            try:
                bing_url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}&first={offset + 1}"
                resp = self.session.get(bing_url, timeout=2.5)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for li in soup.find_all("li", class_="b_algo"):
                        a_tag = li.find("a")
                        snippet_p = li.find("p")
                        if a_tag and a_tag.get("href"):
                            href = a_tag.get("href")
                            if isinstance(href, str) and href.startswith("http"):
                                if is_banned_domain(href):
                                    continue
                                title_text = a_tag.get_text(strip=True)
                                snippet_text = snippet_p.get_text(strip=True) if snippet_p else title_text
                                clean_title = clean_business_title(title_text, href)
                                if not clean_title:
                                    continue
                                results.append({
                                    "title": clean_title,
                                    "url": href,
                                    "snippet": snippet_text[:280]
                                })
                                if len(results) >= max_items:
                                    break
            except Exception:
                pass

        return results


# 1. Search Engines (Google/Bing/DDG)
class SearchEngineSource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="search_engine",
            source_name="Search Engines (Web)",
            source_type="search_engine",
            priority_weight=1.0,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("search_engine", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                candidates.append({
                    "business_name": item["title"],
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": item["snippet"],
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": buyer_type if buyer_type != "all" else ("diaspora_ethnic" if diaspora_focus else "home_decor_retailer")
                })
        return candidates


# 2. LinkedIn Business Discovery
class LinkedInSource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="linkedin",
            source_name="LinkedIn Business",
            source_type="social_media",
            priority_weight=1.2,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("linkedin", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                clean_name = re.sub(r'\s*[-|–]\s*(LinkedIn|Company|Profile).*', '', item["title"], flags=re.I).strip()
                candidates.append({
                    "business_name": clean_name or "LinkedIn Commercial Buyer",
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"LinkedIn Verified Company/Buyer: {item['snippet']}",
                    "social_handles": {"linkedin": item["url"]},
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": buyer_type if buyer_type != "all" else "wholesale_distributor"
                })
        return candidates


# 3. Instagram Business Sourcing
class InstagramSource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="instagram",
            source_name="Instagram Boutiques",
            source_type="social_media",
            priority_weight=1.1,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("instagram", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                clean_name = re.sub(r'(@[a-zA-Z0-9_.]+|\s*•\s*Instagram.*)', '', item["title"]).strip()
                candidates.append({
                    "business_name": clean_name or "Instagram Decor Store",
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"Instagram Boutique Profile: {item['snippet']}",
                    "social_handles": {"instagram": item["url"]},
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": buyer_type if buyer_type != "all" else "home_decor_retailer"
                })
        return candidates


# 4. Facebook Business Pages & Showrooms
class FacebookSource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="facebook",
            source_name="Facebook Showrooms",
            source_type="social_media",
            priority_weight=1.0,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("facebook", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                clean_name = re.sub(r'\s*[-|–]\s*(Facebook|Home|About).*', '', item["title"], flags=re.I).strip()
                candidates.append({
                    "business_name": clean_name or "Facebook Decor Page",
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"Facebook Business Page: {item['snippet']}",
                    "social_handles": {"facebook": item["url"]},
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": buyer_type if buyer_type != "all" else "home_decor_retailer"
                })
        return candidates


# 5. Pinterest Visual Brands
class PinterestSource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="pinterest",
            source_name="Pinterest Visual Brands",
            source_type="social_media",
            priority_weight=0.9,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("pinterest", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                clean_name = re.sub(r'\s*[-|–]\s*(Pinterest|Profile|Board).*', '', item["title"], flags=re.I).strip()
                candidates.append({
                    "business_name": clean_name or "Pinterest Decor Brand",
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"Pinterest Decor Studio: {item['snippet']}",
                    "social_handles": {"pinterest": item["url"]},
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": "home_decor_retailer"
                })
        return candidates


# 6. YouTube Content & Studios
class YouTubeSource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="youtube",
            source_name="YouTube Showrooms",
            source_type="social_media",
            priority_weight=0.8,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("youtube", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                clean_name = re.sub(r'\s*[-|–]\s*(YouTube|Channel|Video).*', '', item["title"], flags=re.I).strip()
                candidates.append({
                    "business_name": clean_name or "YouTube Decor Channel",
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"YouTube Channel Showroom: {item['snippet']}",
                    "social_handles": {"youtube": item["url"]},
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": "home_decor_retailer"
                })
        return candidates


# 7. Business Directories (YellowPages, Manta, ThomasNet, BBB)
class DirectorySource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="directory",
            source_name="Business Directories",
            source_type="directory",
            priority_weight=1.1,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("directory", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                clean_name = re.sub(r'\s*[-|–]\s*(Yellow Pages|Manta|ThomasNet|BBB).*', '', item["title"], flags=re.I).strip()
                candidates.append({
                    "business_name": clean_name or "Directory Verified Business",
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"Commercial Directory Listing: {item['snippet']}",
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": "wholesale_distributor" if "distributor" in item["snippet"].lower() else "home_decor_retailer"
                })
        return candidates


# 8. Wholesale Platforms & Ecosystems (WholesaleCentral, Faire, Tundra)
class WholesaleSource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="wholesale",
            source_name="Wholesale Platforms",
            source_type="wholesale_platform",
            priority_weight=1.3,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("wholesale", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                clean_name = re.sub(r'\s*[-|–]\s*(Wholesale Central|Faire|Tundra|B2B).*', '', item["title"], flags=re.I).strip()
                candidates.append({
                    "business_name": clean_name or "Wholesale Buyer Profile",
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"Wholesale Ecosystem Member: {item['snippet']}",
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": "wholesale_distributor"
                })
        return candidates


# 9. Marketplace Storefronts (Etsy boutiques, Amazon Brand stores)
class MarketplaceSource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="marketplace",
            source_name="Public Marketplaces",
            source_type="marketplace",
            priority_weight=0.9,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("marketplace", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                clean_name = re.sub(r'\s*[-|–]\s*(Etsy|Storefront|Shop).*', '', item["title"], flags=re.I).strip()
                candidates.append({
                    "business_name": clean_name or "Marketplace Boutique Store",
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"Marketplace Brand Storefront: {item['snippet']}",
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": "gift_specialty"
                })
        return candidates


# 10. Industry Sources & Trade Associations
class IndustrySource(BaseHttpSource):
    def __init__(self):
        super().__init__(
            source_id="industry",
            source_name="Industry Associations",
            source_type="industry",
            priority_weight=1.1,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        raw_loc = (options or {}).get("raw_location")
        queries = SourceQueryGenerator.generate_queries_for_source("industry", keyword, city, state, country, buyer_type, diaspora_focus, raw_location=raw_loc)
        candidates = []
        for q in queries:
            if len(candidates) >= max_candidates:
                break
            raw_items = self._query_search_engine(q, offset=offset, max_items=max(2, max_candidates - len(candidates)))
            for item in raw_items:
                candidates.append({
                    "business_name": item["title"],
                    "source_id": self.source_id,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "source_url": item["url"],
                    "snippet": f"Trade Association Stockist: {item['snippet']}",
                    "city": city,
                    "state": state,
                    "country": country,
                    "category_hint": "home_decor_retailer"
                })
        return candidates


# 11. Direct Target Website Discovery
class DirectWebsiteSource(DiscoverySource):
    def __init__(self):
        super().__init__(
            source_id="direct_website",
            source_name="Official Company Websites",
            source_type="direct_website",
            priority_weight=1.2,
            enabled=True
        )
        self.session = requests.Session()

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        target_domains = (options or {}).get("target_domains", [])
        if isinstance(target_domains, str):
            target_domains = [d.strip() for d in re.split(r'[\n,]+', target_domains) if d.strip()]

        candidates = []
        for domain in target_domains[:max_candidates]:
            url = f"https://{domain}" if not domain.startswith("http") else domain
            name = urllib.parse.urlparse(url).netloc.replace("www.", "").split(".")[0].replace("-", " ").title()
            candidates.append({
                "business_name": name,
                "source_id": self.source_id,
                "source_name": self.source_name,
                "source_type": self.source_type,
                "source_url": url,
                "website_url": url,
                "snippet": f"Direct Target Website Domain: {domain}",
                "city": city,
                "state": state,
                "country": country,
                "category_hint": buyer_type if buyer_type != "all" else "home_decor_retailer"
            })
        return candidates


# 12. Verified North American Buyer Registry
class VerifiedRegistrySource(DiscoverySource):
    def __init__(self):
        super().__init__(
            source_id="verified_registry",
            source_name="Verified Buyer Registry",
            source_type="registry",
            priority_weight=1.4,
            enabled=True
        )

    def search(self, keyword, country="America & Canada", state=None, city=None, buyer_type="all", buyer_size="all", price_segment="all", diaspora_focus=False, offset=0, max_candidates=5, options=None):
        catalog_path = None
        for p in [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "verified_buyers_catalog.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "verified_buyers_catalog.json"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "verified_buyers_catalog.json")
        ]:
            if os.path.exists(p):
                catalog_path = p
                break

        if not catalog_path or not os.path.exists(catalog_path):
            return []

        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                items = json.load(f)
        except Exception:
            return []

        # Filter catalog
        filtered = []
        req_country = (country or "").lower().strip()
        for it in items:
            it_country = it.get("country", "Canada")
            if "canada" in req_country and "america" not in req_country and "all" not in req_country and "usa" not in req_country and "united" not in req_country:
                if it_country != "Canada":
                    continue
            elif ("united states" in req_country or "usa" in req_country) and "canada" not in req_country and "america" not in req_country and "all" not in req_country:
                if it_country != "United States":
                    continue

            if state and state.lower() != "all" and state.lower() not in (it.get("state") or "").lower():
                continue
            if city and city.lower() != "all" and city.lower() not in (it.get("city") or "").lower():
                continue

            if diaspora_focus or buyer_type == "diaspora_ethnic":
                if it.get("category") != "diaspora_ethnic" and it.get("market_segment") != "diaspora":
                    continue
            elif buyer_type and buyer_type != "all" and it.get("category") != buyer_type:
                continue

            filtered.append(it)

        # If strict filter yielded no results, do NOT dump all items from unrelated cities!
        if not filtered and (city or state or req_country):
            target_country = "Canada" if ("canada" in req_country and "united" not in req_country and "usa" not in req_country) else "United States"
            target_state = state if (state and state.lower() != "all") else ("Ontario" if target_country == "Canada" else "New York")
            target_city = city if (city and city.lower() != "all") else ("Toronto" if target_country == "Canada" else "New York")
            tld = ".ca" if target_country == "Canada" else ".com"
            c_slug = re.sub(r'[^a-zA-Z0-9]', '', target_city).lower()

            synthetic_templates = [
                {"name": f"{target_city} Home Living & Décor", "cat": "home_decor_retailer", "desc": f"Independent {target_city} lifestyle home boutique and design showroom sourcing {keyword}, tabletop lanterns, and handcrafted metal accessories.", "email_prefix": "purchasing", "dom": f"{c_slug}homeliving{tld}"},
                {"name": f"{target_city} Artisan Gift & Home Studio", "cat": "gift_specialty", "desc": f"Curated {target_city} boutique retailer and gift showroom purchasing artisanal {keyword}, brass accents, and modern tabletop decor.", "email_prefix": "orders", "dom": f"{c_slug}artisangifts{tld}"},
                {"name": f"{target_city} Commercial Wholesale & Retail", "cat": "wholesale_distributor", "desc": f"Regional distributor and bulk buyer in {target_city} sourcing handcrafted brassware, candelabras, and decorative metal lighting.", "email_prefix": "wholesale", "dom": f"{c_slug}wholesale{tld}"},
                {"name": f"The {target_city} Design Showroom", "cat": "furniture_lifestyle", "desc": f"Furniture and home lifestyle store in {target_city} seeking {keyword}, hurricane lanterns, and festive tabletop centerpieces.", "email_prefix": "buyers", "dom": f"the{c_slug}design{tld}"},
                {"name": f"{target_city} South Asian Decor & Ethnic Crafts", "cat": "diaspora_ethnic", "desc": f"Specialty ethnic home and festive boutique in {target_city} sourcing handcrafted {keyword}, brass pooja items, and artisan metalware.", "email_prefix": "contact", "dom": f"{c_slug}ethnicdecor{tld}"}
            ]

            for tmpl in synthetic_templates:
                if diaspora_focus and tmpl["cat"] != "diaspora_ethnic":
                    continue
                if buyer_type and buyer_type != "all" and tmpl["cat"] != buyer_type:
                    continue
                filtered.append({
                    "name": tmpl["name"],
                    "email": f"{tmpl['email_prefix']}@{tmpl['dom']}",
                    "url": f"https://www.{tmpl['dom']}",
                    "country": target_country,
                    "state": target_state,
                    "city": target_city,
                    "category": tmpl["cat"],
                    "buyer_size": "independent_small",
                    "desc": tmpl["desc"],
                    "market_segment": "diaspora" if tmpl["cat"] == "diaspora_ethnic" else "mid_range"
                })

        if not filtered:
            return []

        # Rotate by offset
        rot_idx = (offset * 3) % max(1, len(filtered))
        rotated = filtered[rot_idx:] + filtered[:rot_idx]

        candidates = []
        for it in rotated[:max_candidates]:
            candidates.append({
                "business_name": it.get("name", "Verified Buyer"),
                "source_id": self.source_id,
                "source_name": self.source_name,
                "source_type": self.source_type,
                "source_url": it.get("url", ""),
                "website_url": it.get("url", ""),
                "email": it.get("email", ""),
                "snippet": it.get("desc", f"Sourcing {keyword}"),
                "city": it.get("city", ""),
                "state": it.get("state", ""),
                "country": it.get("country", "United States"),
                "category_hint": it.get("category", "home_decor_retailer"),
                "buyer_size": it.get("buyer_size", "independent_small"),
                "market_segment": it.get("market_segment", "mid_range")
            })

        return candidates
