"""
buyer_scorer.py - Comprehensive Multi-Factor Commercial Buyer Scoring Engine
Calculates the 100-point Final Buyer Score combining Business Relevance, Buyer Intent,
Product Compatibility, Geographic Match, Business Authenticity, Contact Quality,
and Cross-Source Confirmation Boosts.
"""

from typing import Dict, Any, Optional
from .product_affinity import ProductAffinityEngine


class BuyerScorer:
    """
    Computes rigorous commercial buyer scores (0-100) for handcrafted metallic candle holders,
    lanterns, and tabletop decor.
    """

    @classmethod
    def calculate_score(
        cls,
        lead: Dict[str, Any],
        keyword: Optional[str] = None,
        target_country: Optional[str] = None,
        target_state: Optional[str] = None,
        target_city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates 100-point composite buyer score and returns score breakdown for any product keyword.
        """
        category = lead.get("category") or lead.get("category_hint") or "home_decor_retailer"
        raw_text = f"{lead.get('business_name', '')} {lead.get('company_name', '')} {lead.get('snippet', '')} {lead.get('raw_content', '')} {lead.get('context_snippet', '')}".lower()

        # 1. Business Relevance (0 to 20 pts)
        relevance_map = {
            "diaspora_ethnic": 20,
            "wholesale_distributor": 20,
            "home_decor_retailer": 18,
            "furniture_lifestyle": 18,
            "gift_specialty": 15,
            "interior_design": 13,
            "hospitality_events": 8
        }
        relevance_score = relevance_map.get(category, 16)

        # 2. Buyer Intent (0 to 15 pts)
        intent_score = 0
        if any(w in raw_text for w in ["wholesale", "distributor", "import", "b2b", "trade account", "volume purchase"]):
            intent_score = 15
        elif any(w in raw_text for w in ["retailer", "stockist", "storefront", "showroom", "multiple locations", "chain"]):
            intent_score = 12
        elif any(w in raw_text for w in ["shop", "store", "boutique", "studio"]):
            intent_score = 10
        else:
            intent_score = 7

        # 3. Product Compatibility (0 to 20 pts)
        compat_eval = ProductAffinityEngine.evaluate_compatibility(
            business_name=lead.get("business_name") or lead.get("company_name", ""),
            content_corpus=raw_text,
            category=category,
            target_keyword=keyword
        )
        compat_score = int((compat_eval["score"] / 100.0) * 20.0)

        # 4. Geographic Match (0 to 10 pts)
        geo_score = 0
        lead_city = (lead.get("city") or "").lower()
        lead_state = (lead.get("state") or "").lower()
        lead_country = (lead.get("country") or "").lower()

        if target_city and target_city.lower() != "all" and target_city.lower() in lead_city:
            geo_score = 10
        elif target_state and target_state.lower() != "all" and target_state.lower() in lead_state:
            geo_score = 9
        elif target_country and target_country.lower() not in ["all", "america & canada"]:
            if target_country.lower() in lead_country:
                geo_score = 7
        else:
            geo_score = 8 if lead_country in ["united states", "canada", "usa"] else 5

        # 5. Business Authenticity (0 to 10 pts)
        auth_score = 0
        has_custom_domain = bool(lead.get("website") or lead.get("website_url") or lead.get("domain"))
        has_phone = bool(lead.get("phone"))
        has_address = bool(lead.get("city") and lead.get("state"))
        if has_custom_domain:
            auth_score += 5
        if has_phone:
            auth_score += 3
        if has_address:
            auth_score += 2
        auth_score = min(10, max(4, auth_score))

        # 6. Contact Quality & Tier (0 to 15 pts)
        lead_tier = lead.get("lead_tier", "")
        email = (lead.get("email") or "").lower()
        contact_score = 0
        if lead_tier.startswith("Tier 1") or any(email.startswith(p) for p in ['procurement', 'buyer', 'sourcing', 'purchasing']):
            contact_score = 15
        elif lead_tier.startswith("Tier 2") or any(email.startswith(p) for p in ['owner', 'founder', 'director', 'sales', 'wholesale']):
            contact_score = 12
        elif email:
            contact_score = 8
        else:
            contact_score = 3

        # 7. Cross-Source Confirmation & Evidence Boosts (0 to 10 pts)
        source_count = lead.get("source_count", 1)
        conf_level = lead.get("cross_source_confidence", "Weak")
        source_score = 0
        if conf_level == "Very Strong" or source_count >= 3:
            source_score = 10
        elif conf_level == "Strong" or source_count >= 2:
            source_score = 8
        elif source_count == 2:
            source_score = 6
        else:
            source_score = 4

        # Evidence micro-boosts (from social/directory signals)
        socials = lead.get("social_profiles") or {}
        if socials and has_custom_domain and compat_eval["is_compatible"]:
            source_score = min(10, source_score + 1)

        final_score = relevance_score + intent_score + compat_score + geo_score + auth_score + contact_score + source_score
        final_score = min(100, max(20, final_score))

        return {
            "buyer_score": final_score,
            "product_compatibility": compat_eval["level"],
            "product_compatibility_score": compat_score,
            "business_authenticity": "High" if auth_score >= 8 else ("Medium" if auth_score >= 5 else "Basic"),
            "cross_source_confidence": conf_level,
            "breakdown": {
                "business_relevance": relevance_score,
                "buyer_intent": intent_score,
                "product_compatibility": compat_score,
                "geographic_match": geo_score,
                "business_authenticity": auth_score,
                "contact_quality": contact_score,
                "cross_source_confidence": source_score
            }
        }
