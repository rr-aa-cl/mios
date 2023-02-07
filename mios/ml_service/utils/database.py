from mongodb_client.mongodb_client import MongoDBClient
from pymongo.mongo_client import MongoClient
from pymongo.errors import DuplicateKeyError


def delete_local_results(agents: list, db: str, skill_class: str, tags: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove(db, skill_class, {"meta.tags": tags })


def delete_local_knowledge(agents: list, db: str, skill_class: str, scope: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove(db, skill_class, {"meta.scope": scope})


def delete_global_results(agent: str, db: str, skill_class: str, tags: list):
    client = MongoDBClient(agent)
    client.remove(db, skill_class, {"meta.tags": tags })


def delete_global_knowledge(agent: str, db: str, skill_class: str, tags: list):
    client = MongoDBClient(agent)
    client.remove(db, skill_class, {"meta.tags": tags })


def backup_result(from_host: str, to_host: str, skill_class: str, uuid: str, dst_col: str):
    from_client = MongoDBClient(from_host)
    to_client = MongoDBClient(to_host)

    result = from_client.read("ml_results", skill_class, {"meta.uuid": uuid})
    to_client.write(dst_col, skill_class, result)


def backup_results(from_host: str, to_host: str, skill_class: str, tags: list, from_db: str = "ml_results",
                   to_db: str = "ml_results"):
    from_client = MongoDBClient(from_host)
    to_client = MongoDBClient(to_host)
    results = from_client.read(from_db, skill_class, {"meta.tags": {"$all": tags}})
    for r in results:
        try:
            to_client.write(to_db, skill_class, r)
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


def load_results(host: str, database: str, skill: str, result_uuid: str, trial: int):
    client = MongoDBClient(host)
    results = client.read(database, skill, {"meta.uuid": result_uuid})[0]
    task_context = results["meta"]["default_context"]
    theta = results["n" + str(trial)]["theta"]
    context_mapping = results["meta"]["domain"]["context_mapping"]

    for t in theta:
        params = context_mapping[t]
        for p in params:
            p_tmp_1 = p.split(".")
            p_tmp_2 = p_tmp_1[-1].split("-")
            if len(p_tmp_2) == 2:
                dim = int(p_tmp_2[-1]) - 1
            else:
                dim = False
            if len(p_tmp_1) == 4:
                if p_tmp_1[0] not in task_context:
                    task_context[p_tmp_1[0]] = dict()
                if p_tmp_1[1] not in task_context[p_tmp_1[0]]:
                    task_context[p_tmp_1[0]][p_tmp_1[1]] = dict()
                if p_tmp_1[2] not in task_context[p_tmp_1[0]][p_tmp_1[1]]:
                    task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]] = dict()

            if len(p_tmp_1) == 4:
                # if p_tmp_2[0] not in task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]]:
                #     task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]][p_tmp_2[0]] = []
                if dim is False:
                    task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]][p_tmp_2[0]] = theta[t]
                else:
                    task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]][p_tmp_2[0]][dim] = theta[t]
            if len(p_tmp_1) == 5:
                if p_tmp_1[3] not in task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]]:
                    task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]][p_tmp_1[3]] = dict()
                # if p_tmp_2[0] not in task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]][p_tmp_1[3]]:
                #     task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]][p_tmp_1[3]][p_tmp_2[0]] = []
                if dim is False:
                    task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]][p_tmp_1[3]][p_tmp_2[0]] = theta[t]
                else:
                    task_context[p_tmp_1[0]][p_tmp_1[1]][p_tmp_1[2]][p_tmp_1[3]][p_tmp_2[0]][dim] = theta[t]

    return task_context
