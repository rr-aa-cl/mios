from definitions.insertion_definitions import insert_key_demo
from utils.experiment_wizard import start_experiment
from services.cmaes import CMAESConfiguration
from utils.udp_client import call_method
from utils.udp_client import start_task
from utils.udp_client import wait_for_task


def learn():
    pd = insert_key_demo("abus_e30", 1)
    config = CMAESConfiguration()
    config.n_ind = 5
    robot = "collective-panda-005.local"
    call_method(robot, 12002, "set_grasped_object", {"object": "key_abus_e30"})
    start_experiment(robot, [robot], pd, config, keep_record=False)


def learn_2():
    robot = "collective-panda-005.local"
    call_method(robot, 12002, "set_grasped_object", {"object": "key_abus_e30"})
    response = start_task(robot, "InsertObject", {
        "parameters":{
            "insertable": "key_abus_e30",
            "insert_into": "lock_abus_e30",
            "insert_approach": "lock_abus_e30_above"
        },
        "skills": {
            "insertion": {
                "control": {
                    "cart_imp": {
                        "K_x": [200, 200, 0, 10, 10, 10]
                    }
                },
                "skill": {
                    "traj_speed": [0.005, 0.2],
                    "time_max": 5.0
                }
            },
            "contact": {
                "skill": {
                    "time_max": 5.0
                }
            }
        }
    })

    wait_for_task(robot, response["result"]["task_uuid"])

    response = start_task(robot, "ExtractObject", {
        "parameters":
            {
                "extractable": "key_abus_e30",
                "extract_from": "lock_abus_e30",
                "extract_to": "lock_abus_e30_above"
            }
    })

    wait_for_task(robot, response["result"]["task_uuid"])

    response = start_task(robot, "InsertObject", {
        "parameters":{
            "insertable": "key_abus_e30",
            "insert_into": "lock_abus_e30",
            "insert_approach": "lock_abus_e30_above",
            "offset": [0.003, -0.002, 0, -5, -5, 0]
        },
        "skills": {
            "insertion": {
                "control": {
                    "cart_imp": {
                        "K_x": [50, 50, 10, 10, 10, 10]
                    }
                },
                "skill": {
                    "traj_speed": [0.02, 0.2],
                    "time_max": 5.0
                }
            },
            "contact": {
                "skill": {
                    "time_max": 5.0
                }
            }
        }
    })

    wait_for_task(robot, response["result"]["task_uuid"])

    response = start_task(robot, "ExtractObject", {
        "parameters":
            {
                "extractable": "key_abus_e30",
                "extract_from": "lock_abus_e30",
                "extract_to": "lock_abus_e30_above"
            }
    })

    wait_for_task(robot, response["result"]["task_uuid"])

    response = start_task(robot, "InsertObject", {
        "parameters":{
            "insertable": "key_abus_e30",
            "insert_into": "lock_abus_e30",
            "insert_approach": "lock_abus_e30_above",
            "offset": [0.001, -0.002, 0, 5, -10, 0]
        },
        "skills": {
            "insertion": {
                "control": {
                    "cart_imp":{
                        "K_x": [200, 200, 10, 10, 10, 10],
                    }
                },
                "skill": {
                    "time_max": 5.0
                }
            },
            "contact": {
                "skill": {
                    "time_max": 5.0
                }
            }
        }
    })

    wait_for_task(robot, response["result"]["task_uuid"])

    response = start_task(robot, "ExtractObject", {
        "parameters":
            {
                "extractable": "key_abus_e30",
                "extract_from": "lock_abus_e30",
                "extract_to": "lock_abus_e30_above"
            }
    })

    wait_for_task(robot, response["result"]["task_uuid"])

    response = start_task(robot, "InsertObject", {
        "parameters":{
            "insertable": "key_abus_e30",
            "insert_into": "lock_abus_e30",
            "insert_approach": "lock_abus_e30_above",
            "offset": [0.00, 0.002, 0, 5, 0, 0]
        },
        "skills": {
            "insertion": {
                "control": {
                    "cart_imp":{
                        "K_x": [200, 200, 100, 10, 10, 10]
                    }
                },
                "skill": {
                    "time_max": 5.0,
                    "traj_speed": [0.01, 0.2]
                }
            },
            "contact": {
                "skill": {
                    "time_max": 5.0
                }
            }
        }
    })

    wait_for_task(robot, response["result"]["task_uuid"])

    response = start_task(robot, "ExtractObject", {
        "parameters":
            {
                "extractable": "key_abus_e30",
                "extract_from": "lock_abus_e30",
                "extract_to": "lock_abus_e30_above"
            }
    })

    wait_for_task(robot, response["result"]["task_uuid"])
    trial_successful()


def trial_successful():
    robot = "collective-panda-005.local"
    call_method(robot, 12002, "set_grasped_object", {"object": "key_abus_e30"})
    response = start_task(robot, "InsertObject", {
        "parameters":{
            "insertable": "key_abus_e30",
            "insert_into": "lock_abus_e30",
            "insert_approach": "lock_abus_e30_above",
            "offset": [0, 0, 0, 0, 5, 0]
        },
        "skills": {
            "insertion": {
                "control": {
                    "cart_imp": {
                        "K_x": [1000, 1000, 1000, 100, 100, 100]
                    }
                },
                "skill": {
                    "time_max": 5.0
                }
            },
            "contact": {
                "skill": {
                    "time_max": 5.0
                }
            }
        }
    })

    wait_for_task(robot, response["result"]["task_uuid"])

    response = start_task(robot, "ExtractObject", {
        "parameters":
            {
                "extractable": "key_abus_e30",
                "extract_from": "lock_abus_e30",
                "extract_to": "lock_abus_e30_above"
            }
    })

    wait_for_task(robot, response["result"]["task_uuid"])