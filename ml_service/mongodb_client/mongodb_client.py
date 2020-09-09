import pymongo
from bson import objectid
from pymongo import MongoClient
import logging

logger = logging.getLogger("ml_service")


class MongoDBClient():
    """Simple Client for MongoDB interaction"""

    def __init__(self, host='localhost', port=27017):
        self.client = MongoClient(host, port)
        logger.info("MongoDB is initialized at " + host + ":" + str(port))

    def read(self, db: str, collection: str, search_param: dict) -> list:
        db_connection = self.client[db]
        col = db_connection[collection]
        findings = []
        for f in col.find(filter=search_param):
            findings.append(f)
        return findings

    def write(self, db: str, collection: str, document: dict or list) -> objectid.ObjectId or list:
        db_connection = self.client[db]
        col = db_connection[collection]
        if isinstance(document, list):
            # document_id = col.insert_many(document).inserted_ids
            document_ids = []
            for doc in document:
                single_id = self._write_single(db, collection, doc)
                document_ids.append(single_id)
        elif isinstance(document, dict):
            document_ids = col.insert_one(document).inserted_id
        else:
            logger.error("Document type is not dict or list, but " + str(type(document)))
            logger.info("Cannot insert document into Database.")
            return False
        return document_ids

    def _write_single(self, db: str, collection: str, document: dict) -> objectid.ObjectId:
        db_connection = self.client[db]
        col = db_connection[collection]
        if isinstance(document, dict):
            return col.insert_one(document).inserted_id
        else:
            logger.error("Document type is not dict, but " + str(type(document)))
            logger.info("Cannot insert document into Database.")
            return False

    def remove(self, db: str, collection: str, search_param: dict) -> bool:
        db_connection = self.client[db]
        col = db_connection[collection]
        result = col.delete_one(search_param, collation=None, session=None)
        if result.deleted_count > 0:
            return True
        else:
            return False

    def update(self, db: str, collection: str, search_param: dict, new_param: dict) -> bool:
        db_connection = self.client[db]
        col = db_connection[collection]
        if isinstance(search_param, dict):
            if isinstance(new_param, dict):
                new_param_set = {"$set": new_param}
                col.update_one(search_param, new_param_set)
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
