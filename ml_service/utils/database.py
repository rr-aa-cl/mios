from mongodb_client.mongodb_client import MongoDBClient


def delete_local_results(agents: list, task_type: str, tags: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove("ml_results", task_type, {"meta.tags": tags})


def delete_local_knowledge(agents: list, task_type: str, tags: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove("local_knowledge", task_type, {"meta.tags": tags})


def delete_global_results(agent: str, task_type: str, tags: list):
    client = MongoDBClient(agent)
    client.remove("global_ml_results", task_type, {"meta.tags": tags})


def delete_global_knowledge(agent: str, task_type: str, tags: list):
    client = MongoDBClient(agent)
    client.remove("global_knowledge", task_type, {"meta.tags": tags})
