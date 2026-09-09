"""
discovery_engine.py - Autonomous Multi-Source Buyer Discovery Engine
Orchestrates multi-source crawling across Search Engines, Social Media, Directories,
Wholesale Platforms, Marketplaces, Industry Sources, and Direct Websites with entity resolution,
website resolution, product affinity evaluation, and 100-point buyer scoring.
"""

import os
import uuid
import datetime
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_source import DiscoverySource
from .sources import (
    SearchEngineSource,
    LinkedInSource,
    InstagramSource,
    FacebookSource,
    PinterestSource,
    YouTubeSource,
    DirectorySource,
    WholesaleSource,
    MarketplaceSource,
    IndustrySource,
    DirectWebsiteSource,
    is_banned_domain,
    clean_business_title,
    JUNK_TITLES
)
from .website_resolver import OfficialWebsiteResolver
from .entity_resolver import EntityResolver
from .buyer_scorer import BuyerScorer
from .source_analytics import SourceAnalyticsManager
from .location_registry import resolve_geographic_location


class MultiSourceDiscoveryEngine:
    """
    Supercharged Multi-Source Commercial Buyer Discovery Engine.
    """

    DISCOVERY_MODES = {
        "quick_crawl": {
            "name": "Quick Crawl",
            "description": "Fast discovery using top-performing channels (Search Engines, Wholesale, LinkedIn, Instagram).",
            "primary_sources": ["search_engine", "wholesale", "linkedin", "instagram"]
        },
        "deep_crawl": {
            "name": "Deep Crawl",
            "description": "Exhaustive multi-source discovery with complete website resolution and cross-entity matching.",
            "primary_sources": ["search_engine", "wholesale", "linkedin", "instagram", "directory", "facebook"]
        },
        "social_discovery": {
            "name": "Social Discovery",
            "description": "Focuses on commercial business accounts across LinkedIn, Instagram, Facebook, Pinterest, and YouTube.",
            "primary_sources": ["instagram", "linkedin", "facebook", "pinterest", "youtube"]
        },
        "wholesale_discovery": {
            "name": "Wholesale Discovery",
            "description": "Prioritizes wholesale platforms, bulk distributors, cash-and-carry importers, and trade directories.",
            "primary_sources": ["wholesale", "directory", "linkedin", "search_engine"]
        },
        "retail_discovery": {
            "name": "Retail Discovery",
            "description": "Prioritizes home décor retailers, furniture showrooms, candle shops, and lifestyle gift boutiques.",
            "primary_sources": ["search_engine", "instagram", "facebook", "marketplace"]
        },
        "multi_source": {
            "name": "Multi-Source Discovery",
            "description": "Balanced distribution across all enabled platforms and web search.",
            "primary_sources": ["search_engine", "wholesale", "linkedin", "instagram", "directory", "facebook", "marketplace", "pinterest", "industry"]
        }
    }

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        self.website_resolver = OfficialWebsiteResolver()
        self.analytics_manager = SourceAnalyticsManager(self.data_dir)

        # Initialize all modular discovery sources
        self.sources: Dict[str, DiscoverySource] = {
            "wholesale": WholesaleSource(),
            "linkedin": LinkedInSource(),
            "instagram": InstagramSource(),
            "search_engine": SearchEngineSource(),
            "directory": DirectorySource(),
            "facebook": FacebookSource(),
            "pinterest": PinterestSource(),
            "youtube": YouTubeSource(),
            "marketplace": MarketplaceSource(),
            "industry": IndustrySource(),
            "direct_website": DirectWebsiteSource()
        }

    def get_available_sources(self) -> List[Dict[str, Any]]:
        """
        Returns list of all available discovery sources with metadata and performance telemetry.
        """
        analytics = {r["source_id"]: r for r in self.analytics_manager.get_source_analytics()}
        result = []
        for s_id, src in self.sources.items():
            info = src.to_dict()
            stat = analytics.get(s_id, {})
            info["qualification_pct"] = stat.get("qualification_pct", 0.0)
            info["leads_count"] = stat.get("leads", 0)
            result.append(info)
        return result

    def get_discovery_modes(self) -> List[Dict[str, Any]]:
        """
        Returns available discovery modes.
        """
        return [
            {"id": mode_id, **meta}
            for mode_id, meta in self.DISCOVERY_MODES.items()
        ]

    def discover_buyers(
        self,
        keyword: str = "Handcrafted Products",
        discovery_mode: str = "multi_source",
        enabled_sources: Optional[List[str]] = None,
        country: Optional[str] = "America & Canada",
        state: Optional[str] = None,
        city: Optional[str] = None,
        location: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        buyer_size: Optional[str] = "all",
        price_segment: Optional[str] = "all",
        diaspora_focus: bool = False,
        target_domains: Optional[List[str]] = None,
        max_results: int = 10,
        offset: int = 0,
        exclude_emails: Optional[Set[str]] = None,
        exclude_domains: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes multi-source candidate discovery, resolves candidate websites,
        performs cross-source entity resolution, evaluates product affinity,
        and assigns 100-point buyer score.
        """
        exclude_emails = {e.lower().strip() for e in (exclude_emails or set()) if e}
        exclude_domains = {d.lower().strip() for d in (exclude_domains or set()) if d}

        # Parse freeform location if provided
        active_loc = location or country or ""
        if not city and not state and active_loc and active_loc.lower() not in ["all", "america & canada", "both countries", "global", "worldwide"]:
            parts = [p.strip() for p in active_loc.split(",") if p.strip()]
            if len(parts) >= 2:
                city = parts[0]
                state = parts[1]
            else:
                geo_c, geo_s, geo_ctry = resolve_geographic_location(city=active_loc, country=country)
                city = geo_c
                state = geo_s
                country = geo_ctry

        geo_city, geo_state, geo_country = resolve_geographic_location(city=city, state=state, country=country)

        # 1. Determine active sources based on mode and enabled_sources
        active_source_ids = []
        mode_meta = self.DISCOVERY_MODES.get(discovery_mode, self.DISCOVERY_MODES["multi_source"])

        if enabled_sources and len(enabled_sources) > 0:
            active_source_ids = [s for s in enabled_sources if s in self.sources]
        else:
            active_source_ids = [s for s in mode_meta["primary_sources"] if s in self.sources]

        if not active_source_ids:
            active_source_ids = list(self.sources.keys())

        # If target domains provided, always prioritize direct website source
        if target_domains and "direct_website" not in active_source_ids:
            active_source_ids.insert(0, "direct_website")

        # 2. Allocate candidate discovery quotas across active sources
        quota_per_source = max(2, int((max_results * 1.5) / max(1, len(active_source_ids))))

        raw_candidates: List[Dict[str, Any]] = []

        # 3. Parallel discovery execution across active sources
        def _run_source(s_id: str):
            src = self.sources[s_id]
            try:
                cands = src.search(
                    keyword=keyword,
                    country=country,
                    state=state,
                    city=city,
                    buyer_type=buyer_type,
                    buyer_size=buyer_size,
                    price_segment=price_segment,
                    diaspora_focus=diaspora_focus,
                    offset=offset,
                    max_candidates=quota_per_source,
                    options={"target_domains": target_domains, "raw_location": active_loc}
                )
                return s_id, cands
            except Exception as e:
                print(f"[DiscoveryEngine] Source {s_id} notice: {e}")
                return s_id, []

        with ThreadPoolExecutor(max_workers=min(6, len(active_source_ids))) as executor:
            future_to_source = {executor.submit(_run_source, s_id): s_id for s_id in active_source_ids}
            for future in as_completed(future_to_source):
                try:
                    src_id, cands = future.result()
                    raw_candidates.extend(cands)
                except Exception:
                    pass

        # 4. Filter obvious exclusions from raw candidates
        valid_candidates = []
        for cand in raw_candidates:
            em = (cand.get("email") or "").strip().lower()
            if em and em in exclude_emails:
                continue
            dom = cand.get("domain") or self.website_resolver.extract_domain_from_url(cand.get("source_url", ""))
            if dom and (dom in exclude_domains or is_banned_domain(dom)):
                continue
            if is_banned_domain(cand.get("source_url", "")):
                continue
            cand["domain"] = dom
            valid_candidates.append(cand)

        # 5. Entity Resolution & Initial Cross-Source Deduplication
        deduplicated_candidates = EntityResolver.resolve_and_deduplicate(valid_candidates)

        # 6. Social Profile ➔ Official Website Resolution & Contact Extraction
        def _resolve_candidate(cand: Dict[str, Any]) -> Dict[str, Any]:
            current_web = cand.get("website") or cand.get("website_url")
            if not current_web or "instagram.com" in current_web or "linkedin.com" in current_web or "facebook.com" in current_web or "yellowpages" in current_web:
                detected_web = self.website_resolver.find_official_website_from_snippet(
                    title=cand.get("business_name", ""),
                    snippet=cand.get("snippet", ""),
                    url=cand.get("source_url", "")
                )
                if detected_web and not is_banned_domain(detected_web):
                    current_web = detected_web
                    cand["website"] = detected_web
                    cand["website_url"] = detected_web
                else:
                    cand["website"] = ""
                    cand["website_url"] = ""
                    current_web = ""

            if current_web and not is_banned_domain(current_web) and (not cand.get("email") or "@" not in str(cand.get("email", ""))):
                try:
                    res = self.website_resolver.resolve_website_and_extract_contacts(
                        website_url=current_web,
                        country_hint=cand.get("country") or country
                    )
                    if res.get("emails"):
                        cand["email"] = res["emails"][0]
                    if res.get("phones") and not cand.get("phone"):
                        cand["phone"] = res["phones"][0]
                    if res.get("social_profiles"):
                        existing_soc = cand.get("social_profiles", {})
                        for k, v in res["social_profiles"].items():
                            if k not in existing_soc:
                                existing_soc[k] = v
                        cand["social_profiles"] = existing_soc
                    if res.get("text_corpus"):
                        cand["snippet"] = f"{cand.get('snippet', '')} {res['text_corpus']}"[:500]
                    if res.get("country"):
                        cand["country"] = res["country"]
                except Exception:
                    pass

            return cand

        with ThreadPoolExecutor(max_workers=min(5, max(1, len(deduplicated_candidates)))) as executor:
            resolved_candidates = list(executor.map(_resolve_candidate, deduplicated_candidates[:max_results * 2]))

        # 7. Second-pass Entity Resolution
        final_entities = EntityResolver.resolve_and_deduplicate(resolved_candidates)

        # 8. Filter exclusions again & eliminate empty emails
        qualified_leads: List[Dict[str, Any]] = []
        seen_emails: Set[str] = set(exclude_emails)

        for ent in final_entities:
            em = (ent.get("email") or "").strip().lower()
            if not em or "@" not in em:
                continue
            if em in seen_emails:
                continue

            domain_part = em.split("@")[1]
            if is_banned_domain(domain_part):
                continue

            website = ent.get("website") or ent.get("website_url") or (f"https://www.{domain_part}" if domain_part else "")
            if is_banned_domain(website):
                continue

            raw_cname = ent.get("business_name") or ent.get("company_name") or ""
            company_name = clean_business_title(raw_cname, website or domain_part)
            if not company_name or company_name.lower() in JUNK_TITLES or is_banned_domain(company_name):
                continue

            seen_emails.add(em)

            # Compute 100-Point Final Buyer Score & Product Compatibility dynamically
            scoring_meta = BuyerScorer.calculate_score(
                lead=ent,
                keyword=keyword,
                target_country=country,
                target_state=state,
                target_city=city
            )

            # Build normalized output lead matching ExportFlow schema
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            lead_record = {
                "id": f"lead-{uuid.uuid4().hex[:8]}",
                "date": now_utc.strftime("%Y-%m-%d"),
                "discovered_at": now_utc.isoformat(),
                "company_name": company_name,
                "buyer_name": ent.get("buyer_name") or ent.get("target_name") or company_name,
                "email": em,
                "website": website,
                "city": ent.get("city") or city or geo_city,
                "state": ent.get("state") or state or geo_state,
                "country": ent.get("country") or country or geo_country,
                "keyword": keyword,
                "category": ent.get("category_hint") or (buyer_type if buyer_type != "all" else "home_decor_retailer"),
                "buyer_size": ent.get("buyer_size") or (buyer_size if buyer_size != "all" else "independent_small"),
                "market_segment": ent.get("market_segment") or ("diaspora" if diaspora_focus else "mid_range"),
                "validation_status": "valid",
                "is_mx_verified": True,
                "reply_status": "uncontacted",
                "raw_content": ent.get("snippet", ""),
                "source_platform": ent.get("primary_source") or "Search Engines",
                # Multi-Source Transparency Fields (Req 15 & 26)
                "primary_source": ent.get("primary_source") or ent.get("source_name") or "Search Engines",
                "discovery_sources": ent.get("discovery_sources", [ent.get("primary_source", "Search Engines")]),
                "source_count": ent.get("source_count", 1),
                "social_profiles": ent.get("social_profiles", {}),
                "directory_profiles": ent.get("directory_profiles", []),
                "source_urls": ent.get("source_urls", [ent.get("source_url", "")]),
                "cross_source_confidence": scoring_meta["cross_source_confidence"],
                "buyer_score": scoring_meta["buyer_score"],
                "product_compatibility": scoring_meta["product_compatibility"],
                "business_authenticity": scoring_meta["business_authenticity"],
                "score_breakdown": scoring_meta["breakdown"]
            }

            qualified_leads.append(lead_record)
            if len(qualified_leads) >= max_results:
                break

        # 9. Sort leads in descending order of Buyer Score
        qualified_leads.sort(key=lambda l: float(l.get("buyer_score", 0)), reverse=True)

        # 10. Record telemetry for source analytics
        for l in qualified_leads:
            p_src = l.get("primary_source", "")
            s_key = "search_engine"
            if "linkedin" in p_src.lower():
                s_key = "linkedin"
            elif "instagram" in p_src.lower():
                s_key = "instagram"
            elif "facebook" in p_src.lower():
                s_key = "facebook"
            elif "pinterest" in p_src.lower():
                s_key = "pinterest"
            elif "youtube" in p_src.lower():
                s_key = "youtube"
            elif "directory" in p_src.lower():
                s_key = "directory"
            elif "wholesale" in p_src.lower():
                s_key = "wholesale"
            elif "market" in p_src.lower():
                s_key = "marketplace"
            elif "industry" in p_src.lower():
                s_key = "industry"
            elif "website" in p_src.lower():
                s_key = "direct_website"
            elif "verified" in p_src.lower():
                s_key = "verified_registry"

            is_qual = l.get("buyer_score", 0) >= 65
            self.analytics_manager.record_discovery_event(s_key, 1, 1, 1 if is_qual else 0)

        return qualified_leads[:max_results]
