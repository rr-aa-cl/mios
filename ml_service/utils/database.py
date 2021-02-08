from mongodb_client.mongodb_client import MongoDBClient
from pymongo.mongo_client import MongoClient
from pymongo.errors import DuplicateKeyError


def delete_local_results(agents: list, db: str, task_type: str, tags: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove(db, task_type, {"meta.tags": tags })


def delete_local_knowledge(agents: list, db: str, task_type: str, tags: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove(db, task_type, {"meta.tags": tags })


def delete_global_results(agent: str, db: str, task_type: str, tags: list):
    client = MongoDBClient(agent)
    client.remove(db, task_type, {"meta.tags": tags })


def delete_global_knowledge(agent: str, db: str, task_type: str, tags: list):
    client = MongoDBClient(agent)
    client.remove(db, task_type, {"meta.tags": tags })


def backup_result(from_host: str, to_host: str, task_type: str, uuid: str, dst_col: str):
    from_client = MongoDBClient(from_host)
    to_client = MongoDBClient(to_host)

    result = from_client.read("ml_results", task_type, {"meta.uuid": uuid})
    to_client.write(dst_col, task_type, result)


def backup_results(from_host: str, to_host: str, task_type: str, tags: list, dst_col: str):
    from_client = MongoDBClient(from_host)
    to_client = MongoDBClient(to_host)
    results = from_client.read("ml_results", task_type, {"meta.tags": {"$all": tags}})
    for r in results:
        try:
            to_client.write(dst_col, task_type, r)
        except DuplicateKeyError:
            print("Skipping duplicate...")


def remove_duplicate_results(host: str, db: str, col: str):
    client = MongoClient(host)
    docs = client[db][col].find({})
    tags = dict()
    for d in docs:
        tag = d["meta"]["tags"]
        if str(tag) in tags:
            tags[str(tag)] += 1
        else:
            tags[str(tag)] = 1

    for tag, cnt in tags.items():
        if cnt > 1:
            print("Found " + str(cnt-1) + " duplicates for tag: " + tag)
            client[db][col].delete_one({"meta.tags": tag.strip('][').replace("'", "").replace(" ", "").split(',')})
