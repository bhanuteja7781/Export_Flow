"""
product_affinity.py - Dynamic Product Compatibility & Affinity Model
Evaluates how closely a business's offerings match ANY commercial product niche
(e.g., metal candle holders, tabletop decor, brass crafts, home decor, furniture, etc.).
"""

import re
from typing import Dict, Any, List, Tuple, Optional


class ProductAffinityEngine:
    """
    Evaluates product compatibility and commercial fit dynamically for ANY product keyword.
    """

    DISQUALIFYING_SIGNALS = [
        "gaming stream", "crypto casino", "forex trading", "nft drop",
        "personal meme", "fan account", "celebrity gossip"
    ]

    @classmethod
    def evaluate_compatibility(
        cls,
        business_name: str,
        content_corpus: str,
        category: str = "home_decor_retailer",
        target_keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates compatibility score (0-100), affinity level ('High', 'Moderate', 'Low'),
        and matched product signals dynamically based on target_keyword.
        """
        combined = f"{business_name} {content_corpus} {category}".lower()

        # Check for immediate disqualification
        for disq in cls.DISQUALIFYING_SIGNALS:
            if re.search(r'\b' + re.escape(disq) + r'\b', combined):
                return {
                    "score": 15,
                    "level": "Disqualified / Irrelevant",
                    "signals": [f"Disqualified: {disq}"],
                    "is_compatible": False
                }

        matched_signals: List[Tuple[str, float]] = []

        # 1. Dynamic matching against target_keyword tokens and n-grams
        if target_keyword and target_keyword.strip():
            kw_clean = target_keyword.lower().strip()
            # Full keyword match
            if kw_clean in combined:
                matched_signals.append((kw_clean, 1.0))

            # Sub-token matches
            tokens = [t for t in re.split(r'[\s,/\-_]+', kw_clean) if len(t) >= 3]
            for tok in tokens:
                if tok in combined:
                    matched_signals.append((tok, 0.85))

        # 2. General commercial intent matches
        commercial_terms = [
            ("wholesale", 0.95),
            ("distributor", 0.95),
            ("supplier", 0.90),
            ("retailer", 0.90),
            ("store", 0.85),
            ("shop", 0.85),
            ("studio", 0.85),
            ("boutique", 0.85),
            ("stockist", 0.90),
            ("b2b", 0.95),
            ("orders", 0.80),
            ("contact", 0.75)
        ]
        for term, weight in commercial_terms:
            if term in combined:
                matched_signals.append((term, weight))

        # Base score from commercial category
        base_score = 75

        # Keyword boost
        if matched_signals:
            top_weights = sorted([w for _, w in matched_signals], reverse=True)[:4]
            boost = sum(w * 6 for w in top_weights)
            final_score = min(100, int(base_score * 0.6 + boost * 1.8))
        else:
            final_score = 65

        if final_score >= 80:
            level = "High"
            is_compat = True
        elif final_score >= 60:
            level = "Moderate"
            is_compat = True
        else:
            level = "Low"
            is_compat = False

        unique_signals = list(dict.fromkeys([kw for kw, _ in matched_signals[:6]]))

        return {
            "score": final_score,
            "level": level,
            "signals": unique_signals,
            "is_compatible": is_compat
        }
