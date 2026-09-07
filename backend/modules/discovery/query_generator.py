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
        Builds a clean location clause from location parameters.
        Supports freeform inputs like "Tuskegee, Alabama", "Austin, Texas", "London, UK", etc.
        """
        if raw_location and str(raw_location).strip() and str(raw_location).lower() not in ["all", "america & canada", "global", "worldwide"]:
            loc_clean = str(raw_location).strip().rstrip(",")
            return loc_clean

        loc_parts = []
        if city and str(city).lower() != "all":
            loc_parts.append(str(city).strip())
        if state and str(state).lower() != "all":
            loc_parts.append(str(state).strip())
        if country and str(country).lower() not in ["all", "america & canada", "global", "worldwide"]:
            loc_parts.append(str(country).strip())

        if loc_parts:
            return ", ".join(loc_parts)
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
        quoted_loc = f'"{loc_str}"' if loc_str else ""

        queries: List[str] = []

        if source_id == "search_engine":
            if loc_part:
                queries.extend([
                    f"{kw} {loc_part}",
                    f"{kw} store {loc_part}",
                    f"{kw} studio {loc_part}",
                    f"{kw} shop {loc_part}",
                    f"{kw} boutique {loc_part}",
                    f"{kw} contact {loc_part}"
                ])
            else:
                queries.extend([
                    f"{kw} wholesale",
                    f"{kw} retailer store",
                    f"{kw} boutique shop",
                    f"{kw} distributor"
                ])

        elif source_id == "linkedin":
            if loc_part:
                queries.extend([
                    f'site:linkedin.com/company "{kw}" {loc_part}',
                    f'site:linkedin.com/in ("buyer" OR "owner" OR "founder") "{kw}" {loc_part}',
                    f'site:linkedin.com "{kw}" {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:linkedin.com/company "{kw}" store',
                    f'site:linkedin.com/in buyer "{kw}"',
                    f'site:linkedin.com/company "{kw}" wholesale'
                ])

        elif source_id == "instagram":
            if loc_part:
                queries.extend([
                    f'site:instagram.com "{kw}" {loc_part}',
                    f'site:instagram.com {kw} shop {loc_part}',
                    f'site:instagram.com {kw} studio {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:instagram.com "{kw}" shop',
                    f'site:instagram.com "{kw}" boutique',
                    f'site:instagram.com "{kw}" studio'
                ])

        elif source_id == "facebook":
            if loc_part:
                queries.extend([
                    f'site:facebook.com "{kw}" {loc_part}',
                    f'site:facebook.com {kw} {loc_part} contact'
                ])
            else:
                queries.extend([
                    f'site:facebook.com "{kw}" store',
                    f'site:facebook.com "{kw}" shop'
                ])

        elif source_id == "pinterest":
            if loc_part:
                queries.extend([
                    f'site:pinterest.com {kw} shop {loc_part}',
                    f'site:pinterest.com "{kw}" {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:pinterest.com "{kw}" store',
                    f'site:pinterest.com "{kw}" brand'
                ])

        elif source_id == "youtube":
            if loc_part:
                queries.extend([
                    f'site:youtube.com {kw} shop {loc_part}',
                    f'site:youtube.com "{kw}" {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:youtube.com "{kw}" tour',
                    f'site:youtube.com "{kw}" showroom'
                ])

        elif source_id == "directory":
            if loc_part:
                queries.extend([
                    f'site:yellowpages.com OR site:yellowpages.ca "{kw}" {loc_part}',
                    f'site:yelp.com OR site:bbb.org "{kw}" {loc_part}',
                    f'site:manta.com {kw} {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:yellowpages.com "{kw}" wholesale',
                    f'site:manta.com "{kw}" store',
                    f'site:thomasnet.com "{kw}"'
                ])

        elif source_id == "wholesale":
            if loc_part:
                queries.extend([
                    f'site:wholesalecentral.com OR site:faire.com "{kw}" {loc_part}',
                    f'{kw} wholesale distributor {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:wholesalecentral.com "{kw}"',
                    f'site:faire.com/brand "{kw}"',
                    f'"{kw}" wholesale b2b'
                ])

        elif source_id == "marketplace":
            if loc_part:
                queries.extend([
                    f'site:etsy.com/shop "{kw}" {loc_part}',
                    f'{kw} storefront {loc_part}'
                ])
            else:
                queries.extend([
                    f'site:etsy.com/shop "{kw}"',
                    f'"{kw}" boutique store'
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
