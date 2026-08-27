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
    Commercial Buyer Classifier and Tier Prioritizer for Handcrafted Metal Candle Holders & Décor.
    """

    BUYER_CATEGORIES = {
        "home_decor_retailer": {
            "label": "Home Décor Retailer",
            "tier": 1,
            "tier_label": "Tier 1: High Potential",
            "description": "Home furnishing stores, décor boutiques, and lifestyle stores."
        },
        "wedding_event_decorator": {
            "label": "Wedding & Event Decorator",
            "tier": 1,
            "tier_label": "Tier 1: High Potential",
            "description": "Wedding décor, event styling, and centerpiece specialists."
        },
        "hospitality_hotel": {
            "label": "Hotels & Hospitality",
            "tier": 1,
            "tier_label": "Tier 1: High Potential",
            "description": "Hotels, resorts, luxury restaurants, and banquet venues."
        },
        "gift_specialty": {
            "label": "Gift & Specialty Store",
            "tier": 1,
            "tier_label": "Tier 1: High Potential",
            "description": "Gift shops, premium gift retailers, and seasonal décor stockists."
        },
        "interior_design": {
            "label": "Interior Design Firm",
            "tier": 2,
            "tier_label": "Tier 2: Strong Potential",
            "description": "Interior designers, commercial stagers, and architectural stylists."
        },
        "event_party_rental": {
            "label": "Event & Party Rental",
            "tier": 2,
            "tier_label": "Tier 2: Strong Potential",
            "description": "Party, wedding, and corporate event rental companies."
        },
        "furniture_lifestyle": {
            "label": "Furniture & Lifestyle Retailer",
            "tier": 2,
            "tier_label": "Tier 2: Strong Potential",
            "description": "Furniture showrooms, lifestyle chains, and accent stores."
        },
        "wholesale_distributor": {
            "label": "Wholesale & Distributor",
            "tier": 3,
            "tier_label": "Tier 3: Distribution",
            "description": "Home décor wholesalers, giftware distributors, and bulk importers."
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
        """
        Classifies leads into the 8 specialized B2B buyer categories.
        """
        if not leads:
            return []

        # Deduplicate list by email
        unique_leads = []
        seen = set()
        for l in leads:
            email = l.get("email", "").lower()
            if email and email not in seen:
                seen.add(email)
                unique_leads.append(dict(l))

        # Try Gemini AI classification first if API key is configured
        if self.client and self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                return self._classify_with_gemini(unique_leads, product_niche)
            except Exception as e:
                print(f"[ClassificationModule] Gemini AI call failed ({e}). Falling back to heuristic classifier.")

        # Deterministic Heuristic Classifier
        return self._classify_with_heuristics(unique_leads, product_niche)

    def _classify_with_gemini(self, leads: List[Dict[str, Any]], product_niche: str) -> List[Dict[str, Any]]:
        """
        Batch-prompts Gemini AI model for multi-class commercial B2B categorization.
        """
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
                "country": l.get("country", ""),
                "platform": l.get("source_platform", "")
            })

        valid_cats = list(self.BUYER_CATEGORIES.keys())
        prompt = f"""
You are an expert B2B buyer categorization specialist. Classify each of these leads for a manufacturer of handcrafted {product_niche} into EXACTLY ONE of these 8 categories:
{json.dumps(valid_cats, indent=2)}

Buyer leads:
{json.dumps(lead_summaries, indent=2)}

Respond with a raw JSON array of objects:
[
  {{ "index": 0, "category": "wedding_event_decorator" }}
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

            cat_meta = self.BUYER_CATEGORIES[cat]
            lead["category"] = cat
            lead["category_label"] = cat_meta["label"]
            lead["tier"] = cat_meta["tier"]
            lead["tier_label"] = cat_meta["tier_label"]
            classified_leads.append(lead)

        return classified_leads

    def _classify_with_heuristics(self, leads: List[Dict[str, Any]], product_niche: str) -> List[Dict[str, Any]]:
        """
        Deterministic multi-class commercial B2B categorization based on business profiles and keywords.
        """
        classified = []
        for lead in leads:
            email = lead.get("email", "").lower()
            company = lead.get("company_name", "")
            name = lead.get("buyer_name", "")
            platform = lead.get("source_platform", "")
            domain = email.split('@')[1] if '@' in email else ""

            text_context = f"{company.lower()} {domain.lower()} {platform.lower()} {lead.get('title', '').lower()}"

            # 1. Wedding & Event Decorators (Tier 1)
            if any(kw in text_context for kw in ["wedding", "event styling", "event design", "wedding decor", "ceremony", "bridal", "floral & event"]):
                category = "wedding_event_decorator"

            # 2. Hotels & Hospitality (Tier 1)
            elif any(kw in text_context for kw in ["hotel", "resort", "restaurant", "banquet", "hospitality", "inn", "lounge", "bistro", "palace"]):
                category = "hospitality_hotel"

            # 3. Gift & Specialty Stores (Tier 1)
            elif any(kw in text_context for kw in ["gift", "specialty", "holiday", "seasonal", "stationery", "apothecary", "village", "books", "indigo", "chapters"]):
                category = "gift_specialty"

            # 4. Interior Design Firms (Tier 2)
            elif any(kw in text_context for kw in ["interior design", "interior designer", "design studio", "staging", "architectural", "home staging", "interiors"]):
                category = "interior_design"

            # 5. Event & Party Rental Companies (Tier 2)
            elif any(kw in text_context for kw in ["rental", "party rental", "event rental", "tent & event", "props", "event hire"]):
                category = "event_party_rental"

            # 6. Furniture & Lifestyle Retailers (Tier 2)
            elif any(kw in text_context for kw in ["furniture", "urban barn", "structube", "mobilia", "eq3", "west elm", "pottery barn", "cb2", "crate and barrel", "arhaus", "room and board", "lifestyle store"]):
                category = "furniture_lifestyle"

            # 7. Wholesalers & Distributors (Tier 3)
            elif any(kw in text_context for kw in ["wholesale", "distributor", "import", "importer", "distribution", "trading", "accent decor", "abbott", "co-op", "two's company", "park designs", "kalalou", "b2b"]):
                category = "wholesale_distributor"

            # 8. Home Décor Retailers (Tier 1) - Default
            else:
                category = "home_decor_retailer"

            cat_meta = self.BUYER_CATEGORIES[category]
            lead["category"] = category
            lead["category_label"] = cat_meta["label"]
            lead["tier"] = cat_meta["tier"]
            lead["tier_label"] = cat_meta["tier_label"]

            # Determine Market Segment (Mid-Range & Volume Commercial vs High-End Luxury)
            if not lead.get("market_segment"):
                if any(kw in text_context for kw in ["luxury", "ultra-luxury", "celebrity", "haute", "bespoke", "couture", "high-end", "exclusive", "atelier", "gallery"]):
                    lead["market_segment"] = "high_end"
                    lead["market_segment_label"] = "High-End & Luxury"
                else:
                    lead["market_segment"] = "mid_range"
                    lead["market_segment_label"] = "Mid-Range & Volume Commercial"
            else:
                lead["market_segment_label"] = "High-End & Luxury" if lead["market_segment"] == "high_end" else "Mid-Range & Volume Commercial"

            # Enrich Intern's Feedback with commercial volume context
            if not lead.get("intern_feedback") or "Prospective B2B candidate" in lead.get("intern_feedback", "") or "Verified active commercial buyer" in lead.get("intern_feedback", ""):
                is_mid = lead.get("market_segment") == "mid_range"
                feedbacks = {
                    "wedding_event_decorator": f"{company}: {'High-volume commercial event decorator sourcing repeatable centerpiece lanterns & candelabras.' if is_mid else 'Luxury event designer for bespoke handcrafted brass candle installations.'}",
                    "hospitality_hotel": f"{company}: {'Commercial restaurant/hotel group sourcing durable ambient candle lanterns & tabletop hardware.' if is_mid else 'Luxury boutique resort sourcing artisan handcrafted bronze hurricane lighting.'}",
                    "gift_specialty": f"{company}: {'Retail gift & home accessories stockist for fast-moving brass votives & candleholders.' if is_mid else 'Curated designer gift boutique for handcrafted metal art & accent candleware.'}",
                    "interior_design": f"{company}: {'Commercial & residential styling firm sourcing functional metal home accents.' if is_mid else 'High-end interior architecture studio curating custom metal tabletop lines.'}",
                    "event_party_rental": f"{company}: High-volume commercial event & party rental warehouse. Prime target for durable metal lanterns & candelabras (large batch orders).",
                    "furniture_lifestyle": f"{company}: {'Mainstream furniture showroom chain sourcing accessible tabletop candle accessories.' if is_mid else 'Upscale modern furniture gallery sourcing designer metal tabletop accents.'}",
                    "wholesale_distributor": f"{company}: Major wholesale distributor & importer for direct container loads (MOQ 500+ pcs) across North American retail networks.",
                    "home_decor_retailer": f"{company}: {'Active commercial home decor & lifestyle store. High recurring order potential for metal candle holders & lanterns.' if is_mid else 'Premier luxury home boutique sourcing artisan handcrafted metal candle accessories.'}"
                }
                lead["intern_feedback"] = feedbacks.get(category, f"{company}: Verified commercial B2B buyer ({cat_meta['label']}) for metal candle holders & lanterns.")

            if not lead.get("follow_ups"):
                lead["follow_ups"] = "Ready for initial catalog outreach dispatch"

            classified.append(lead)

        return classified
