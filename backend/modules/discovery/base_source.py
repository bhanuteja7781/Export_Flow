"""
base_source.py - Abstract Base Class for Modular Discovery Sources
Defines the uniform interface for all buyer discovery sources.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class DiscoverySource(ABC):
    """
    Abstract Base Class for modular buyer discovery sources.
    Every source (search engine, social media, directory, wholesale platform, etc.)
    inherits from this class.
    """

    def __init__(
        self,
        source_id: str,
        source_name: str,
        source_type: str,
        priority_weight: float = 1.0,
        enabled: bool = True
    ):
        self.source_id = source_id
        self.source_name = source_name
        self.source_type = source_type  # 'search_engine', 'social_media', 'directory', 'wholesale', 'marketplace', 'industry', 'direct_website', 'registry'
        self.priority_weight = priority_weight
        self.enabled = enabled

    @abstractmethod
    def search(
        self,
        keyword: str,
        country: Optional[str] = "America & Canada",
        state: Optional[str] = None,
        city: Optional[str] = None,
        buyer_type: Optional[str] = "all",
        buyer_size: Optional[str] = "all",
        price_segment: Optional[str] = "all",
        diaspora_focus: bool = False,
        offset: int = 0,
        max_candidates: int = 5,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Discovers raw candidate businesses from this source.
        Returns a list of candidate dictionaries with at least:
        {
            'business_name': str,
            'source_id': str,
            'source_name': str,
            'source_type': str,
            'source_url': str,
            'domain': str (optional),
            'website_url': str (optional),
            'snippet': str,
            'city': str (optional),
            'state': str (optional),
            'country': str (optional),
            'email': str (optional),
            'phone': str (optional),
            'social_handles': dict (optional),
            'category_hint': str (optional),
            'raw_data': dict (optional)
        }
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "priority_weight": self.priority_weight,
            "enabled": self.enabled
        }
