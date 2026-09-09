"""
query_generator.py - Universal Dynamic Query Generator for Any Product & Location
Generates intelligent, highly targeted search queries combining any product/business keyword,
buyer intent, and geographic parameters tailored specifically for each platform.
"""

from typing import List, Dict, Any, Optional


class SourceQueryGenerator:
    """
    Builds platform-optimized search dorks and query strings for ANY commercial product or business niche.
    """

    @classmethod
    def clean_location_string(
        cls,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        raw_location: Optional[str] = None
    ) -> str:
        """
        Builds a clean, search-engine-friendly location clause.
        """
        if city and str(city).strip().lower() not in ["all", "all cities", ""]:
            return str(city).strip()
        if state and str(state).strip().lower() not in ["all", "all states/provinces", ""]:
            return str(state).strip()
        if raw_location and str(raw_location).strip() and str(raw_location).lower() not in ["all", "america & canada", "both countries", "global", "worldwide"]:
            return str(raw_location).strip().split(",")[0].strip()
        if country and str(country).strip().lower() not in ["all", "america & canada", "both countries", "global", "worldwide"]:
            return str(country).strip()
        return ""

    @classmethod
    def generate_queries_for_source(
        cls,
        source_id: str,
        keyword: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        diaspora_focus: bool = False,
        raw_location: Optional[str] = None
    ) -> List[str]:
        """
        Generates dynamic tailored queries for ANY product/business keyword and ANY location across all discovery channels.
        """
        kw = (keyword or "Handcrafted Products").strip()
        loc_str = cls.clean_location_string(city, state, country, raw_location)
        loc_part = f"{loc_str}" if loc_str else ""

        queries: List[str] = []

        if source_id == "search_engine":
            if loc_part:
                queries.extend([
                    f'"{kw}" boutique store {loc_part}',
                    f'home decor boutique {loc_part}',
                    f'home decor stores {loc_part}',
                    f'gift shop boutique {loc_part}'
                ])
            else:
                queries.extend([
                    f'"{kw}" wholesale store',
                    f'home decor boutique retailer',
                    f'gift and lifestyle store'
                ])

        elif source_id == "wholesale":
            if loc_part:
                queries.extend([
                    f'"{kw}" wholesale showroom {loc_part}',
                    f'home decor wholesale distributor {loc_part}',
                    f'home decor trade showroom {loc_part}'
                ])
            else:
                queries.extend([
                    f'"{kw}" wholesale distributor showroom',
                    f'home decor wholesale supplier'
                ])

        elif source_id == "directory":
            if loc_part:
                queries.extend([
                    f'home decor gift boutique {loc_part}',
                    f'curated home boutique {loc_part}',
                    f'specialty home gift store {loc_part}'
                ])
            else:
                queries.extend([
                    f'"{kw}" boutique shop',
                    f'home decor gift store'
                ])

        elif source_id == "linkedin":
            if loc_part:
                queries.extend([
                    f'site:linkedin.com/company "{kw}" {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:linkedin.com/company "{kw}" store'
                ])

        elif source_id == "instagram":
            if loc_part:
                queries.extend([
                    f'site:instagram.com "{kw}" {loc_part}',
                    f'site:instagram.com home decor boutique {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:instagram.com "{kw}" boutique'
                ])

        elif source_id == "facebook":
            if loc_part:
                queries.extend([
                    f'site:facebook.com "{kw}" {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:facebook.com "{kw}" store'
                ])

        elif source_id == "pinterest":
            if loc_part:
                queries.extend([
                    f'site:pinterest.com {kw} boutique {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:pinterest.com "{kw}" decor'
                ])

        elif source_id == "youtube":
            if loc_part:
                queries.extend([
                    f'site:youtube.com "{kw}" showroom {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:youtube.com "{kw}" showroom'
                ])

        elif source_id == "directory":
            if loc_part:
                queries.extend([
                    f'{kw} gift boutique store {loc_part}'
                ])
            else:
                queries.extend([
                    f'{kw} wholesale directory store'
                ])

        elif source_id == "wholesale":
            if loc_part:
                queries.extend([
                    f'{kw} wholesale showroom distributor {loc_part}'
                ])
            else:
                queries.extend([
                    f'{kw} wholesale distributor showroom'
                ])

        elif source_id == "marketplace":
            if loc_part:
                queries.extend([
                    f'{kw} boutique storefront {loc_part}'
                ])
            else:
                queries.extend([
                    f'{kw} boutique showroom'
                ])

        elif source_id == "industry":
            if loc_part:
                queries.extend([
                    f'{kw} association directory {loc_part}',
                    f'{kw} stockist {loc_part}'
                ])
            else:
                queries.extend([
                    f'"{kw} association" member directory',
                    f'"{kw}" retailer directory'
                ])

        cleaned = [q.strip() for q in queries if q.strip()]
        return cleaned or [f"{kw} {loc_part}".strip()]
