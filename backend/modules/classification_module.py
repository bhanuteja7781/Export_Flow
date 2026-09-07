"""
classification_module.py - AI & Heuristic Commercial Buyer Classifier and Sizing Engine
Specialized for Handcrafted Metal Candle Holders, Lanterns & Tabletop Décor
Classifies buyers into:
- Diaspora & Ethnic Decor / Indian Handicrafts (High Priority)
- Wholesale Distributors, Importers & Cash-and-Carry (High Priority)
- Home Décor Retailers & Boutiques (High Priority)
- Furniture & Home Furnishings Stores (High Priority)
- Gift & Specialty Stores (Mid Priority)
- Interior Design Studios (Mid Priority)
- Hotels & Event Stylists (De-prioritized / Specialized)

Also categorizes Buyer Scale & Size:
- Enterprise / Large Wholesaler (Container MOQs, multi-state distribution)
- Mid-Market Regional Chain (3-20 stores, quarterly reorders)
- Independent Retailer / Diaspora Store (High conversion, accessible owners)
- High-End Studio / Luxury Showroom (Bespoke custom lines)
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

try:
    from google import genai  # type: ignore
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class AIClassificationModule:
    """
    Commercial Buyer Classifier, Sizing Engine, and Tier Prioritizer.
    """

    BUYER_CATEGORIES = {
        "diaspora_ethnic": {
            "label": "Diaspora & Indian Handicrafts",
            "tier": 1,
            "tier_label": "Tier 1: High Potential (Diaspora)",
            "description": "Indian home decor, brass pooja/mandir decor, ethnic lifestyle, and festive gift stockists."
        },
        "wholesale_distributor": {
            "label": "Wholesale Distributor & Importer",
            "tier": 1,
            "tier_label": "Tier 1: High Potential (Wholesale)",
            "description": "Home décor wholesalers, bulk importers, and cash-and-carry distributors."
        },
        "home_decor_retailer": {
            "label": "Home Décor Retailer",
            "tier": 1,
            "tier_label": "Tier 1: High Potential (Retail)",
            "description": "Home furnishing stores, décor boutiques, and lifestyle stores."
        },
        "furniture_lifestyle": {
            "label": "Furniture & Home Furnishings",
            "tier": 1,
            "tier_label": "Tier 1: High Potential (Furniture)",
            "description": "Furniture showrooms, home accent stores, and lifestyle chains."
        },
        "gift_specialty": {
            "label": "Gift & Specialty Store",
            "tier": 2,
            "tier_label": "Tier 2: Strong Potential",
            "description": "Gift shops, seasonal décor stockists, and tabletop boutiques."
        },
        "interior_design": {
            "label": "Interior Design Studio",
            "tier": 2,
            "tier_label": "Tier 2: Strong Potential",
            "description": "Interior designers, commercial stagers, and architectural stylists."
        },
        "hospitality_events": {
            "label": "Hotels & Event Stylists",
            "tier": 3,
            "tier_label": "Tier 3: Specialized",
            "description": "Hotels, wedding decorators, and event rental companies."
        }
    }

    BUYER_SIZES = {
        "enterprise_large": {
            "label": "Enterprise / Large Wholesaler",
            "description": "Multi-state distributor or major chain (500+ MOQ container loads)."
        },
        "mid_market": {
            "label": "Mid-Market Regional Store",
            "description": "Regional chain (3–20 stores, consistent repeat quarterly orders)."
        },
        "independent_small": {
            "label": "Independent / Diaspora Boutique",
            "description": "Single or dual location store with rapid purchase decision cycle."
        },
        "high_end_boutique": {
            "label": "High-End Studio / Showroom",
            "description": "Curated luxury showroom or high-end bespoke designer."
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client: Any = None
        if self.api_key and GENAI_AVAILABLE and self.api_key != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[ClassificationModule] GenAI client init notice: {e}")

    def classify_leads(self, leads: List[Dict[str, Any]], product_niche: str = "Metal Candle Holders") -> List[Dict[str, Any]]:
        if not leads:
            return []

        # Deduplicate list by email
        unique_leads = []
        seen = set()
        for l in leads:
            email = (l.get("email") or "").lower()
            if email and email not in seen:
                seen.add(email)
                unique_leads.append(dict(l))
            elif not email:
                unique_leads.append(dict(l))

        # Try Gemini AI classification first if API key is configured
        if self.client and self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                return self._classify_with_gemini(unique_leads, product_niche)
            except Exception as e:
                print(f"[ClassificationModule] Gemini AI call notice ({e}). Falling back to heuristic classifier.")

        # Deterministic Heuristic Classifier
        return self._classify_with_heuristics(unique_leads, product_niche)

    def _classify_with_gemini(self, leads: List[Dict[str, Any]], product_niche: str) -> List[Dict[str, Any]]:
        if not self.client:
            return self._classify_with_heuristics(leads, product_niche)

        lead_summaries = []
        for idx, l in enumerate(leads):
            lead_summaries.append({
                "index": idx,
                "name": l.get("buyer_name", ""),
                "company": l.get("company_name", ""),
                "email": l.get("email", ""),
                "website": l.get("website", ""),
                "city": l.get("city", ""),
                "state": l.get("state", ""),
                "country": l.get("country", ""),
                "platform": l.get("source_platform", "")
            })

        valid_cats = list(self.BUYER_CATEGORIES.keys())
        valid_sizes = list(self.BUYER_SIZES.keys())

        prompt = f"""
You are an expert international B2B buyer categorization specialist for a manufacturer of handcrafted {product_niche}, brass candle lanterns, and metal home accessories.
Classify each lead into EXACTLY ONE category:
{json.dumps(valid_cats, indent=2)}

And assign EXACTLY ONE buyer size:
{json.dumps(valid_sizes, indent=2)}

Buyer leads:
{json.dumps(lead_summaries, indent=2)}

Respond with a raw JSON array of objects:
[
  {{ "index": 0, "category": "diaspora_ethnic", "buyer_size": "independent_small", "market_segment": "diaspora" }}
]
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
        except Exception:
            try:
                response = self.client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                )
            except Exception:
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\n", "", raw_text)
            raw_text = re.sub(r"\n```$", "", raw_text)

        parsed_results = json.loads(raw_text)
        result_map = {item["index"]: item for item in parsed_results if "index" in item}

        classified_leads = []
        for idx, lead in enumerate(leads):
            res = result_map.get(idx, {})
            cat = res.get("category", "home_decor_retailer")
            if cat not in self.BUYER_CATEGORIES:
                cat = "home_decor_retailer"

            size = res.get("buyer_size", "independent_small")
            if size not in self.BUYER_SIZES:
                size = "independent_small"

            cat_meta = self.BUYER_CATEGORIES[cat]
            size_meta = self.BUYER_SIZES[size]

            lead["category"] = cat
            lead["category_label"] = cat_meta["label"]
            lead["tier"] = cat_meta["tier"]
            lead["tier_label"] = cat_meta["tier_label"]
            lead["buyer_size"] = size
            lead["buyer_size_label"] = size_meta["label"]

            if not lead.get("market_segment"):
                lead["market_segment"] = res.get("market_segment", "diaspora" if cat == "diaspora_ethnic" else ("volume_wholesale" if cat == "wholesale_distributor" else "mid_range"))

            lead["market_segment_label"] = (
                "Diaspora & Ethnic" if lead["market_segment"] == "diaspora" else
                "High-Volume Wholesale" if lead["market_segment"] == "volume_wholesale" else
                "High-End & Luxury" if lead["market_segment"] == "high_end" else
                "Mid-Range & Commercial"
            )

            # Enrich intern feedback
            lead["intern_feedback"] = self._generate_intern_feedback(lead, cat, size)
            if not lead.get("follow_ups"):
                lead["follow_ups"] = "Ready for initial catalog outreach dispatch"

            classified_leads.append(lead)

        return classified_leads

    def _classify_with_heuristics(self, leads: List[Dict[str, Any]], product_niche: str) -> List[Dict[str, Any]]:
        classified = []
        for lead in leads:
            email = (lead.get("email") or "").lower()
            company = lead.get("company_name", "")
            platform = lead.get("source_platform", "")
            title = lead.get("title", "")
            city = lead.get("city", "")
            state = lead.get("state", "")
            domain = email.split('@')[1] if '@' in email else ""

            text_context = f"{company.lower()} {domain.lower()} {platform.lower()} {title.lower()} {city.lower()} {state.lower()} {lead.get('raw_content', '').lower()}"

            # 1. Diaspora & Indian Handicrafts / Ethnic Decor (Tier 1 - Top Priority)
            diaspora_keywords = [
                "india", "indian", "desi", "pooja", "puja", "mandir", "diwali", "handicrafts",
                "ethnic", "saffron", "artesia", "edison", "iselin", "brampton", "surrey", "devon",
                "jackson heights", "sugar land", "namaste", "hindu", "brassware", "diya", "vedic",
                "south asian", "rajasthan", "jaipur", "moradabad", "ayurveda", "bazaar", "heritage crafts",
                "indian decor", "rangoli", "urli", "candelabra", "festive decor"
            ]
            if any(kw in text_context for kw in diaspora_keywords):
                category = "diaspora_ethnic"
                buyer_size = "independent_small"
                market_segment = "diaspora"

            # 2. Wholesalers, Importers & Bulk Distributors (Tier 1 - Top Priority)
            elif any(kw in text_context for kw in ["wholesale", "distributor", "import", "importer", "distribution", "trading", "b2b", "cash and carry", "warehouse", "direct import", "accent decor", "abbott", "park designs"]):
                category = "wholesale_distributor"
                buyer_size = "enterprise_large" if any(w in text_context for w in ["national", "global", "group", "corp", "inc", "supply", "enterprise", "direct"]) else "mid_market"
                market_segment = "volume_wholesale"

            # 3. Furniture & Home Furnishings Showrooms (Tier 1 - Top Priority)
            elif any(kw in text_context for kw in ["furniture", "furnishings", "structube", "mobilia", "eq3", "west elm", "pottery barn", "cb2", "crate and barrel", "arhaus", "room and board", "urban barn", "furniture gallery", "accent furniture", "tabletop showroom"]):
                category = "furniture_lifestyle"
                buyer_size = "mid_market" if any(w in text_context for w in ["chain", "stores", "locations", "studios"]) else "independent_small"
                market_segment = "mid_range"

            # 4. Gift & Specialty Stores (Tier 2)
            elif any(kw in text_context for kw in ["gift", "specialty", "holiday", "seasonal", "stationery", "apothecary", "village", "books", "indigo", "chapters", "giftware"]):
                category = "gift_specialty"
                buyer_size = "independent_small"
                market_segment = "mid_range"

            # 5. Interior Design Studios & Stagers (Tier 2)
            elif any(kw in text_context for kw in ["interior design", "interior designer", "design studio", "staging", "architectural", "home staging", "interiors"]):
                category = "interior_design"
                buyer_size = "high_end_boutique" if any(w in text_context for w in ["luxury", "bespoke", "haute", "couture", "celebrity"]) else "independent_small"
                market_segment = "high_end" if buyer_size == "high_end_boutique" else "mid_range"

            # 6. Hotels & Event Stylists (Tier 3 - De-prioritized)
            elif any(kw in text_context for kw in ["hotel", "resort", "restaurant", "banquet", "hospitality", "wedding", "event styling", "event rental", "party rental"]):
                category = "hospitality_events"
                buyer_size = "independent_small"
                market_segment = "mid_range"

            # 7. Home Décor Retailers & Independent Lifestyle Boutiques (Tier 1 - Default)
            else:
                category = "home_decor_retailer"
                buyer_size = "independent_small"
                market_segment = "mid_range"

            cat_meta = self.BUYER_CATEGORIES[category]
            size_meta = self.BUYER_SIZES[buyer_size]

            lead["category"] = category
            lead["category_label"] = cat_meta["label"]
            lead["tier"] = cat_meta["tier"]
            lead["tier_label"] = cat_meta["tier_label"]
            lead["buyer_size"] = lead.get("buyer_size") or buyer_size
            lead["buyer_size_label"] = self.BUYER_SIZES.get(lead["buyer_size"], size_meta)["label"]

            lead["market_segment"] = lead.get("market_segment") or market_segment
            lead["market_segment_label"] = (
                "Diaspora & Ethnic" if lead["market_segment"] == "diaspora" else
                "High-Volume Wholesale" if lead["market_segment"] == "volume_wholesale" else
                "High-End & Luxury" if lead["market_segment"] == "high_end" else
                "Mid-Range & Commercial"
            )

            # Generate structured intern feedback note
            lead["intern_feedback"] = self._generate_intern_feedback(lead, category, lead["buyer_size"])
            if not lead.get("follow_ups"):
                lead["follow_ups"] = "Ready for initial catalog outreach dispatch"

            classified.append(lead)

        return classified

    def _generate_intern_feedback(self, lead: Dict[str, Any], category: str, size: str) -> str:
        company = lead.get("company_name", "Buyer")
        loc_str = f" in {lead.get('city')}, {lead.get('state')}" if lead.get("city") and lead.get("state") else ""

        if category == "diaspora_ethnic":
            return f"{company}{loc_str}: Prime South Asian diaspora stockist for handcrafted brass candle holders, diya lanterns, mandir & festive Diwali home decor collections."
        elif category == "wholesale_distributor":
            return f"{company}{loc_str}: B2B wholesale distributor & direct importer. High recurring order potential for container loads (MOQ 300+ pcs) across North American retail channels."
        elif category == "furniture_lifestyle":
            return f"{company}{loc_str}: Furniture & home accent showroom. Ideal candidate for tabletop metal candle holders, centerpiece lighting, and modern hurricane lanterns."
        elif category == "home_decor_retailer":
            return f"{company}{loc_str}: Active commercial home décor store. Strong candidate for seasonal handcrafted metalware and accent candleware lines."
        elif category == "gift_specialty":
            return f"{company}{loc_str}: Specialty gift & lifestyle boutique for fast-moving brass votives, candle accessories, and seasonal tabletop gifts."
        elif category == "interior_design":
            return f"{company}{loc_str}: Design studio sourcing curated metal accents for commercial and residential styling projects."
        else:
            return f"{company}{loc_str}: Verified North American commercial buyer for metal candle holders & home accessories."
