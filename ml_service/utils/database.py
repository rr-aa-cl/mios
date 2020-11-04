from mongodb_client.mongodb_client import MongoDBClient


def delete_local_results(agents: list, task_type: str, tags: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove("ml_results", task_type, {"meta.tags": {"$all": tags }})


def delete_local_knowledge(agents: list, task_type: str, tags: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove("local_knowledge", task_type, {"meta.tags": {"$all": tags }})


def delete_global_results(agent: str, task_type: str, tags: list):
    client = MongoDBClient(agent)
    client.remove("global_ml_results", task_type, {"meta.tags": {"$all": tags }})


def delete_global_knowledge(agent: str, task_type: str, tags: list):
    client = MongoDBClient(agent)
    client.remove("global_knowledge", task_type, {"meta.tags": {"$all": tags }})


def backup_result(from_host: str, to_host: str, task_type: str, uuid: str, dst_col: str):
    from_client = MongoDBClient(from_host)
    to_client = MongoDBClient(to_host)

    result = from_client.read("ml_results", task_type, {"meta.uuid": uuid})
    to_client.write(dst_col, task_type, result)


def backup_results(from_host: str, to_host: str, task_type: str, tags: list, dst_col: str):
    from_client = MongoDBClient(from_host)
    to_client = MongoDBClient(to_host)
    results = from_client.read("ml_results", task_type, {"meta.tags": {"$all": tags}})
    to_client.write(dst_col, task_type, results)
