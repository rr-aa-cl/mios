from ws_client import *


def unlock_door(host: str = "collective-panda-prime.local"):
    response = start_task(host, "InsertObject", {
        "parameters": {
            "insertable": "key_old",
            "insert_into": "lock_old",
            "insert_approach": "lock_old_approach",
            "offset": [0, 0, 0, 0, 0, 0]
        }
    }
               )

    print(response)
    wait_for_task(host, response["result"]["task_uuid"])
    start_skill(host, "Turn",{"phi": 1.0, "dphi": 0.6, "objects": {"turnable": "EndEffector"}}, {"control_mode": 0},
                {"F_ext_max" : [20, 2]})


def start_skill(address: str, skill: str, parameters: dict, control: dict, user: dict):
    response = start_task(address, "GenericTask", parameters={"parameters": {
        "skill_names": ["skill"],
        "skill_types": [skill]
    },
        "skills": {
            "skill": {
                "skill": parameters,
                "control": control,
                "user": user
            }
        }})
