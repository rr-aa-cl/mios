from typing import Any, List, Union
from .knowledge_store import KnowledgeStore

class DictKnowledgeStore(KnowledgeStore):
    """Pure in-memory KnowledgeStore for testing (Phase 4b)."""

    def __init__(self):
        # Key: (db, collection), Value: list of dicts
        self._data: dict[tuple, list[dict]] = {}

    def read(self, db: str, collection: str, search_param: dict) -> List[dict]:
        docs = self._data.get((db, collection), [])
        results = []
        for doc in docs:
            match = True
            for k, v in search_param.items():
                # Simplified matching for test purposes (full query logic not needed)
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(doc)
        return results

    def write(self, db: str, collection: str, document: Union[dict, List[dict]]) -> Union[str, List[str]]:
        if (db, collection) not in self._data:
            self._data[(db, collection)] = []
        
        if isinstance(document, list):
            ids = []
            for d in document:
                self._data[(db, collection)].append(d)
                ids.append(str(id(d)))
            return ids
        else:
            self._data[(db, collection)].append(document)
            return str(id(document))

    def update(self, db: str, collection: str, search_param: dict, update_param: dict) -> bool:
        # Simplified update (overwrite for tests)
        self.remove(db, collection, search_param)
        self.write(db, collection, update_param)
        return True

    def remove(self, db: str, collection: str, search_param: dict) -> bool:
        if (db, collection) not in self._data:
            return False
        
        initial_len = len(self._data[(db, collection)])
        self._data[(db, collection)] = [
            doc for doc in self._data[(db, collection)]
            if not all(doc.get(k) == v for k, v in search_param.items())
        ]
        return len(self._data[(db, collection)]) < initial_len
