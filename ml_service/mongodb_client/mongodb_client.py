import pymongo
from bson import objectid
from pymongo import MongoClient
from typing import Optional, Union
import logging


import pymongo.errors

logger = logging.getLogger("ml_service")


class MongoDBClient():
    """Simple Client for MongoDB interaction"""

    def __init__(self, host: str='localhost', port: int=27017, max_retry: int=3):
        self.client = MongoClient(host, port)
        self.max_retry = max_retry
        logger.info("MongoDB is initialized at " + host + ":" + str(port))

    def read(self, db: str, collection: str, search_param: dict,
             timeout: Optional[float] = None) -> list:
        # Work on a copy so the caller's dict is never mutated (Phase 1 fix)
        query = dict(search_param)
        try:
            db_connection = self.client[db]
            col = db_connection[collection]
            findings: list = []
            for key in list(query.keys()):
                value = query[key]
                # Apply $all for tag-based list queries
                if key in ("tags", "meta.tags"):
                    if isinstance(value, list):
                        query[key] = {"$all": value}
                # Check key existence when no value supplied
                if not value and value != 0:
                    query[key] = {"$exists": True}
                # Convert string _id to ObjectId
                if key == "_id" and isinstance(query[key], str):
                    query[key] = objectid.ObjectId(query[key])
            for f in col.find(filter=query):
                f["_id"] = str(f["_id"])
                findings.append(f)
            return findings
        except pymongo.errors.ServerSelectionTimeoutError as e:
            logger.error("host not reachable: %s", e)
            return []

    def write(self, db: str, collection: str,
              document: Union[dict, list]) -> Union[str, list, bool]:
        db_connection = self.client[db]
        col = db_connection[collection]
        if isinstance(document, list):
            document_ids: list = []
            for doc in document:
                single_id = self._write_single(db, collection, doc)
                document_ids.append(single_id)
            return document_ids
        elif isinstance(document, dict):
            return self._write_single(db, collection, document)
        else:
            logger.error("Document type is not dict or list, but %s", type(document))
            logger.info("Cannot insert document into Database.")
            return False

    def _write_single(self, db: str, collection: str, document: dict) -> objectid.ObjectId:
        db_connection = self.client[db]
        col = db_connection[collection]
        if isinstance(document, dict):
            if "_id" in document.keys():  # if _id is given as string  ->  ObjectId
                if isinstance(document["_id"],str):
                    document["_id"] = objectid.ObjectId(document["_id"])
            return str(col.insert_one(document).inserted_id)
        else:
            logger.error("Document type is not dict, but " + str(type(document)))
            logger.info("Cannot insert document into Database.")
            return False

    def remove(self, db: str, collection: str, search_param: dict) -> bool:
        # Work on a copy so the caller's dict is never mutated (Phase 1 fix)
        query = dict(search_param)
        db_connection = self.client[db]
        col = db_connection[collection]
        if "_id" in query and isinstance(query["_id"], str):
            query["_id"] = objectid.ObjectId(query["_id"])
        for key in list(query.keys()):
            value = query[key]
            # Phase 1 fix: was `if key == "tags" or "meta.tags"` which is ALWAYS
            # True (truthy string). Now correctly checks key membership.
            if key in ("tags", "meta.tags"):
                if isinstance(value, list):
                    query[key] = {"$all": value}
        result = col.delete_many(query, collation=None, session=None)
        return result.deleted_count > 0

    def update(self, db: str, collection: str, search_param: dict, new_param: dict) -> bool:
        db_connection = self.client[db]
        col = db_connection[collection]
        if isinstance(search_param, dict):
            if "_id" in search_param.keys():  # if _id is given as string  ->  ObjectId
                if isinstance(search_param["_id"], str):
                    search_param["_id"] = objectid.ObjectId(search_param["_id"])
            if isinstance(new_param, dict):
                if new_param.get("_id", False):
                    new_param.pop("_id")
                new_param_set = {"$set": new_param}
                col.update_one(search_param, new_param_set, upsert=False)
            else:
                logger.error("new parameter for update are not dict, but " + str(type(new_param)))
                return False
        else:
            logger.error("search parameter for update are not dict, but " + str(type(new_param)))
            return False
        return True

    def delete_collection(self, db: str, collection: str):
        db_connection = self.client[db]
        col = db_connection[collection]
        col.drop()

    def get_collections(self, db:str) -> list:
        db_connection = self.client[db]
        return db_connection.list_collection_names(filter={})
