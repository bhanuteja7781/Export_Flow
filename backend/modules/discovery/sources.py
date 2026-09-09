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
import base64
import urllib.parse
from typing import List, Dict, Any, Optional, Set, Tuple
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings()

from .base_source import DiscoverySource
from .query_generator import SourceQueryGenerator
from .location_registry import resolve_geographic_location


BANNED_PLATFORM_DOMAINS = {
    # Major consumer marketplaces & platforms
    "amazon.com", "amazon.ca", "amazon.co.uk", "ebay.com", "ebay.ca", "walmart.com", "walmart.ca",
    "target.com", "etsy.com", "wayfair.com", "overstock.com", "alibaba.com", "aliexpress.com",
    "temu.com", "shein.com", "faire.com", "tundra.com", "abound.com", "globalsources.com",
    "dhgate.com", "wish.com", "poshmark.com", "mercari.com", "costco.com", "homedepot.com",
    "lowes.com", "ikea.com", "crateandbarrel.com", "potterybarn.com", "westelm.com", "cb2.com",
    "bedbathandbeyond.com", "kohls.com", "macys.com", "nordstrom.com", "tjmaxx.com", "marshalls.com",
    # Job boards & career platforms
    "indeed.com", "glassdoor.com", "ziprecruiter.com", "monster.com", "careerbuilder.com",
    "simplyhired.com", "salary.com", "payscale.com",
    # Social media & content networks
    "instagram.com", "facebook.com", "linkedin.com", "pinterest.com", "youtube.com",
    "tiktok.com", "twitter.com", "x.com", "reddit.com", "quora.com", "medium.com", "tumblr.com",
    "wikipedia.org", "wikimedia.org", "tripadvisor.com",
    # Generic search engines, portals, aggregators
    "google.com", "bing.com", "duckduckgo.com", "yahoo.com", "yelp.com", "yellowpages.com",
    "yellowpages.ca", "bbb.org", "manta.com", "mapquest.com", "whitepages.com", "superpages.com",
    "wix.com", "wixpress.com", "shopify.com", "myshopify.com", "squarespace.com",
    "wordpress.com", "wordpress.org", "weebly.com", "godaddy.com", "sentry.io", "cloudflare.com",
    # App stores & software download mirrors
    "apkpure.com", "play.google.com", "apps.apple.com", "apkcombo.com", "aptoide.com", "softonic.com", "cnet.com",
    # Dictionaries, media, real estate, generic big box
    "cambridge.org", "merriam-webster.com", "dictionary.com", "thefreedictionary.com", "britannica.com",
    "wordreference.com", "wiktionary.org", "helpfulprofessor.com", "lifestylestores.com", "msn.com",
    "nytimes.com", "washingtonpost.com", "imdb.com", "realtor.com", "homes.com", "zillow.com", "redfin.com",
    "bestbuy.com", "athome.com",
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
        "tiktok", "twitter", "sentry", "cloudflare", "wixpress", "myshopify", "indeed", "glassdoor",
        "ziprecruiter"
    ]
    return any(kw in dom for kw in banned_keywords)

def clean_business_title(raw_title: str, url: str) -> Optional[str]:
    if not raw_title:
        raw_title = ""
    clean = re.sub(r'https?://[^\s]+', '', raw_title).strip()
    clean = re.sub(r'^[a-zA-Z0-9.-]+\.(?:com|ca|org|net|io|co|us|biz|edu|gov)\s*', '', clean).strip()
    clean = re.split(r'\s+[-–|—:]\s+', clean)[0].strip()
    if not clean or len(clean) < 3 or clean.lower() in JUNK_TITLES:
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

    def _extract_stores_from_guide(self, guide_url: str, max_extract: int = 4) -> List[Dict[str, str]]:
        stores: List[Dict[str, str]] = []
        try:
            resp = self.session.get(guide_url, timeout=2.0, verify=False)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            guide_domain = urllib.parse.urlparse(guide_url).netloc.replace("www.", "")
            banned = [guide_domain, "google", "facebook", "instagram", "twitter", "pinterest", "youtube", "tiktok", "amazon", "ebay", "yelp", "aboutads"]
            for a in soup.find_all("a", href=True):
                href_attr = a.get("href", "")
                if not href_attr or not isinstance(href_attr, str):
                    continue
                href = href_attr
                if href.startswith("http") and not any(b in href for b in banned) and not is_banned_domain(href):
                    netloc = urllib.parse.urlparse(href).netloc.replace("www.", "")
                    if "." in netloc and len(netloc) > 4:
                        clean_t = clean_business_title(a.get_text(strip=True), href)
                        if clean_t:
                            snippet_text = a.get_text(strip=True)
                            if a.parent:
                                p_text = a.parent.get_text(strip=True)
                                if len(p_text) > len(snippet_text):
                                    snippet_text = p_text[:250]
                            stores.append({
                                "title": clean_t,
                                "url": f"https://{netloc}",
                                "snippet": snippet_text or f"Curated retail stockist: {clean_t}"
                            })
                            if len(stores) >= max_extract:
                                break
        except Exception:
            pass
        return stores

    def _query_search_engine(self, query: str, offset: int = 0, max_items: int = 4) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        seen_urls: Set[str] = set()
        guides_parsed = 0

        # 1. Primary Strategy: Fast Direct DDG HTML Endpoint (~0.6s)
        try:
            url = "https://html.duckduckgo.com/html/"
            resp = self.session.post(
                url,
                data={"q": query},
                headers={"User-Agent": random.choice(self.USER_AGENTS), "Content-Type": "application/x-www-form-urlencoded"},
                timeout=3.0,
                verify=False
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for r in soup.find_all("div", class_="result__body"):
                    a = r.find("a", class_="result__url") or r.find("a", class_="result__snippet") or r.find("a")
                    title_tag = r.find("h2") or r.find("a", class_="result__a")
                    snippet_tag = r.find("a", class_="result__snippet")
                    if not a or not a.get("href"):
                        continue
                    raw_href_attr = a.get("href")
                    if not raw_href_attr or not isinstance(raw_href_attr, str):
                        continue
                    raw_href = raw_href_attr
                    if "duckduckgo.com/l/?" in raw_href or "uddg=" in raw_href:
                        qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                        real_url = qs.get("uddg", [raw_href])[0]
                    else:
                        real_url = raw_href

                    if not real_url.startswith("http") or real_url in seen_urls:
                        continue

                    # If this is a curated guide or editorial article, extract direct stores (max 1 guide per query)
                    if guides_parsed < 1 and any(term in real_url.lower() for term in ["/story/", "/article/", "/post/", "best-", "top-", "guide"]):
                        guides_parsed += 1
                        guide_stores = self._extract_stores_from_guide(real_url, max_extract=3)
                        for gs in guide_stores:
                            if gs["url"] not in seen_urls:
                                seen_urls.add(gs["url"])
                                results.append(gs)
                                if len(results) >= max_items:
                                    return results

                    if is_banned_domain(real_url):
                        continue

                    title_text = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)
                    clean_t = clean_business_title(title_text, real_url)
                    if not clean_t:
                        continue

                    snippet_text = snippet_tag.get_text(strip=True) if snippet_tag else ""
                    seen_urls.add(real_url)
                    results.append({
                        "title": clean_t,
                        "url": real_url,
                        "snippet": snippet_text[:300]
                    })
                    if len(results) >= max_items:
                        return results
        except Exception:
            pass

        # 2. Secondary Strategy: Bing Search with base64 url decode
        if len(results) < max_items:
            try:
                bing_url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}&cc=US&setlang=en-US&first={offset + 1}"
                resp = self.session.get(bing_url, timeout=3.0, verify=False)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for li in soup.find_all("li", class_="b_algo"):
                        a_tag = li.find("a")
                        snippet_p = li.find("p") or li.find("div", class_="b_caption")
                        if not a_tag or not a_tag.get("href"):
                            continue
                        href = a_tag.get("href")
                        if not isinstance(href, str) or not href.startswith("http"):
                            continue

                        actual_url = href
                        if "bing.com/ck/a" in href and "u=" in href:
                            try:
                                qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                                u_val = qs.get("u", [""])[0]
                                if u_val.startswith("a1"):
                                    clean_b64 = u_val[2:]
                                    rem = len(clean_b64) % 4
                                    if rem == 2:
                                        clean_b64 += "=="
                                    elif rem == 3:
                                        clean_b64 += "="
                                    elif rem == 1:
                                        clean_b64 = clean_b64[:-1]
                                    dec = base64.urlsafe_b64decode(clean_b64).decode("utf-8", errors="ignore")
                                    if dec.startswith("http"):
                                        actual_url = dec
                            except Exception:
                                pass

                        if is_banned_domain(actual_url) or actual_url in seen_urls:
                            continue

                        # If this is a curated guide or editorial article, extract direct stores
                        if guides_parsed < 1 and any(term in actual_url.lower() for term in ["/story/", "/article/", "/post/", "best-", "top-", "guide"]):
                            guides_parsed += 1
                            guide_stores = self._extract_stores_from_guide(actual_url, max_extract=3)
                            for gs in guide_stores:
                                if gs["url"] not in seen_urls:
                                    seen_urls.add(gs["url"])
                                    results.append(gs)
                                    if len(results) >= max_items:
                                        return results

                        title_text = a_tag.get_text(strip=True)
                        snippet_text = snippet_p.get_text(strip=True) if snippet_p else title_text
                        clean_title = clean_business_title(title_text, actual_url)
                        if not clean_title:
                            continue

                        seen_urls.add(actual_url)
                        results.append({
                            "title": clean_title,
                            "url": actual_url,
                            "snippet": snippet_text[:300]
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

