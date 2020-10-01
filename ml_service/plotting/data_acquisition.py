from mongodb_client.mongodb_client import MongoDBClient
import logging
from plotting.result import Result

logger = logging.getLogger("ml_service")


class DataNotFoundError(Exception):
    pass


def get_experiment_data(host: str, task_type: str, type: str = "local", filter: dict = None, uuid: str = None):
    db_client = MongoDBClient(host)
    if type == "local":
        results_db = "ml_results"
    elif type == "global":
        results_db = "global_ml_results"
    else:
        results_db = "none"

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


def get_multiple_experiment_data(host: str, task_type: str, type: str = "local", filter: dict = None):
    db_client = MongoDBClient(host)
    if type == "local":
        results_db = "ml_results"
    elif type == "global":
        results_db = "global_ml_results"
    else:
        results_db = "none"

    if filter is None:
        filter = {}
    docs = db_client.read(results_db, task_type, filter)

    if len(docs) == 0:
        raise DataNotFoundError

    results = []
    for d in docs:
        results.append(Result(d))

    return results
