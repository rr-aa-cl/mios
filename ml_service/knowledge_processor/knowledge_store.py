from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

class KnowledgeStore(ABC):
    """Abstract persistence backend for knowledge records (Introduced in Phase 4b)."""

    @abstractmethod
    def read(self, db: str, collection: str, search_param: dict) -> List[dict]:
        """Read documents matching search_param from the store."""
        pass

    @abstractmethod
    def write(self, db: str, collection: str, document: Union[dict, List[dict]]) -> Union[str, List[str]]:
        """Write one or more documents to the store. Returns ID(s)."""
        pass

    @abstractmethod
    def update(self, db: str, collection: str, search_param: dict, update_param: dict) -> bool:
        """Update documents matching search_param with update_param."""
        pass

    @abstractmethod
    def remove(self, db: str, collection: str, search_param: dict) -> bool:
        """Remove documents matching search_param from the store."""
        pass
