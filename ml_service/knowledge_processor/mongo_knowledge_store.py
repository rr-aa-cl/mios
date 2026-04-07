from typing import List, Union
from .knowledge_store import KnowledgeStore
from mongodb_client.mongodb_client import MongoDBClient

class MongoKnowledgeStore(KnowledgeStore):
    """MongoDB implementation of KnowledgeStore (Added in Phase 4b)."""

    def __init__(self, client: MongoDBClient):
        self._client = client

    def read(self, db: str, collection: str, search_param: dict) -> List[dict]:
        return self._client.read(db, collection, search_param)

    def write(self, db: str, collection: str, document: Union[dict, List[dict]]) -> Union[str, List[str]]:
        return self._client.write(db, collection, document)

    def update(self, db: str, collection: str, search_param: dict, update_param: dict) -> bool:
        return self._client.update(db, collection, search_param, update_param)

    def remove(self, db: str, collection: str, search_param: dict) -> bool:
        return self._client.remove(db, collection, search_param)
