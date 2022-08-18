from mongodb_client.mongodb_client import MongoDBClient
import logging
from plotting.result import Result
from plotting.result import Knowledge

logger = logging.getLogger("ml_service")


class DataNotFoundError(Exception):
    pass


def get_experiment_data(host: str, task_type: str, results_db: str = "ml_results", filter: dict = None, uuid: str = None):
    db_client = MongoDBClient(host, max_retry=1)

    if filter is not None:
        docs = db_client.read(results_db, task_type, filter)
    elif uuid is not None:
        docs = db_client.read(results_db, task_type, {"meta.uuid": uuid})
    else:
        raise DataNotFoundError

    if len(docs) == 0:
        raise DataNotFoundError
    if len(docs) > 1:
        raise DataNotFoundError

    return Result(docs[0])


def get_multiple_experiment_data(host: str, task_type: str, results_db: str = "ml_results", filter: dict = None):
    db_client = MongoDBClient(host)

    if filter is None:
        filter = {}
    docs = db_client.read(results_db, task_type, filter)
    
    if len(docs) == 0:
        raise DataNotFoundError

    results = []
    for d in docs:
        results.append(Result(d))
    return results

def get_multiple_knowledge_data(host: str, task_type: str, type: str = "local", filter: dict = None):
    db_client = MongoDBClient(host)
    if type == "local":
        knowledge_db = "local_knowledge"
    elif type == "global":
        knowledge_db = "global_knowledge"
    else:
        knowledge_db = "local_knowledge"

    if filter is None:
        filter = {}
    docs = db_client.read(knowledge_db, task_type, filter)

    if len(docs) == 0:
        raise DataNotFoundError

    results = []
    for d in docs:
        results.append(Knowledge(d))

    return results
