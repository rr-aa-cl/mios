#!/usr/bin/python3 -u
import time
import numpy as np

from utils.ws_client import *
from xmlrpc.client import ServerProxy
from utils.database import load_results
import csv


class Task:
    def __init__(self, robot):
        self.skill_names = []
        self.skill_types = []
        self.skill_context = dict()

        self.robot = robot
        self.task_uuid = "INVALID"
        self.t_0 = 0

    def add_skill(self, name, type, context):
        self.skill_names.append(name)
        self.skill_types.append(type)
        self.skill_context[name] = context

    def start(self, queue: bool = False):
        self.t_0 = time.time()
        response = start_task(self.robot, "GenericTask", parameters={
            "parameters": {
                "skill_names": self.skill_names,
                "skill_types": self.skill_types,
                "as_queue": queue
            },
            "skills": self.skill_context
        })
        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid)
        print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result


def start_skill(address: str, skill: str, parameters: dict, control: dict, user: dict = {}, skill_name: str = "skill"):
    response = start_task(address, "GenericTask", parameters={"parameters": {
        "skill_names": [skill_name],
        "skill_types": [skill]
    },
        "skills": {
            "skill": {
                "skill": parameters,
                "control": control,
                "user": user
            }
        }})
    return response


def tax_test_grab(robot="collective-panda-008.local"):
    grab_context = {
        "skill": {
            "objects": {
                "Retract": "iros_key_grab_retract",
                "Approach": "iros_key_grab_approach",
                "Grabbable": "iros_key"
            },
            "time_max": 5,
            "approach_speed": [0.5, 1],
            "approach_acc": [1, 4],
            "grab_speed": [0.17, 0.8],
            "grab_acc": [0.35, 0.94],
            "grasp_width": 0.032,
            "grasp_speed": 1.6,
            "grasp_force": 30,
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [1138, 1138, 1338, 167, 167, 167]
            }
        },
        "user": {
            "env_X": [0.005, 0.02]
        }
    }

    t = Task(robot)
    t.add_skill("grab", "TaxGrab", grab_context)
    t.start()
    result = t.wait()
    print(result)


def tax_test_place(robot="collective-panda-008.local"):
    call_method(robot, 12000, "set_grasped_object", {"object": "iros_key"})
    place_context = {
        "skill": {
            "objects": {
                "Retract": "iros_key_grab_retract",
                "Approach": "iros_key_grab_approach",
                "Placeable": "iros_key",
                "Surface": "iros_key_storage"
            },
            "approach_speed": [0.5, 1],
            "approach_acc": [1, 4.0],
            "place_speed": [0.18, 1],
            "place_acc": [1, 2.2],
            "release_width": 0.06,
            "release_speed": 4.6,
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 150, 150, 150]
            }
        },
        "user": {
            "env_X": [0.01, 0.02]
        }
    }
    t = Task(robot)
    t.add_skill("place", "TaxPlace", place_context)
    t.start()
    result = t.wait()
    print(result)


def tax_test_turn(robot="collective-panda-008.local"):
    call_method(robot, 12000, "set_grasped_object", {"object": "iros_key"})
    turn_context = {
        "skill": {
            "objects": {
                "Turnable": "iros_key",
                "GoalOrientation": "iros_turn_goal"
            },
            "turn_speed": [0.5, 2.5],
            "turn_acc": [2, 25.0]},
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [665, 665, 665, 173, 173, 173]
            }
        },
        "user": {
            "env_X": [0.01, 0.02]
        }
    }
    turn_back_context = {
        "skill": {
            "objects": {
                "Turnable": "iros_key",
                "GoalOrientation": "iros_lock"
            },
            "turn_speed": [0.2, 2.5],
            "turn_acc": [0.5, 30.0]},
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        },
        "user": {
            "env_X": [0.01, 0.02]
        }
    }

    # turn_context = load_results("collective-control-001.local", "iros2021", "turn", "f15ea299-7057-4953-80a3-c90c1d1b2919" , 149)

    t = Task(robot)
    t.add_skill("turn", "TaxTurn", turn_context)
    t.add_skill("turn_back", "TaxTurn", turn_back_context)
    t.start()
    result = t.wait()
    print(result)


def test_tax_press_button(robot="collective-panda-008.local"):
    start_skill(robot, "TaxPressButton",
                {"objects": {"Button": "iros_button", "Approach": "iros_button_approach"},
                 "approach_speed": [0.05, 0.5], "approach_acc": [0.5, 1.0],
                 "press_speed": [0.05, 0.5], "press_acc": [0.5, 1.0], "duration": 2,
                 "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                 "ROI_phi": [0, 0, 0, 0, 0, 0],
                 "condition_level_success": "External",
                 "condition_level_error": "External"
                 },
                {"control_mode": 0},
                {
                    "env_X": [0.005, 0.1]
                })


def tax_test_move(robot):
    move1_context = {
        "skill": {
            "objects": {
                "GoalPose": "move_1"
            },
            "speed": [0.05, 1],
            "acc": [0.5, 5]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        }
    }
    t = Task(robot)
    t.add_skill("move", "TaxMove", move1_context)
    t.start()


def tax_test_insertion(robot):
    call_method(robot, 12000, "set_grasped_object", {"object": "iros_key"})
    insertion_context = {
        "skill": {
            "objects": {
                "Container": "iros_lock",
                "Approach": "iros_lock_approach",
                "Insertable": "iros_key"
            },
            "approach_speed": [0.5, 1],
            "approach_acc": [1, 4],
            "insertion_speed": [0.4, 0.077],
            "insertion_acc": [0.78, 1.62],
            "f_max_push": 10,
            "search_a": [5, 6, 4, 1.15, 1.5, 0],
            "search_f": [2, 1, 0.6, 0.7, 0.87, 0],
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0],
            "stuck_dx_thr": 0.035
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [1004, 536, 1617, 17, 35, 68]
            }
        },
        "user": {
            "env_X": [0.02, 0.04]
        }
    }
    # insertion_context = load_results("collective-control-001.local", "iros2021", "insert_object",
    #                                     "62cb816d-7d22-48bd-9eb8-dd4440b1fe5f", 244)["skills"]["insertion"]
    # insertion_context["skill"]["objects"]["Insertable"] = "iros_key"
    # insertion_context["skill"]["objects"]["Container"] = "iros_lock"
    # insertion_context["skill"]["objects"]["Approach"] = "iros_lock_approach"
    #
    # print(insertion_context)
    t = Task(robot)
    t.add_skill("insertion", "TaxInsertion", insertion_context)
    t.start()
    result = t.wait()
    print(result)


def tax_test_button_press(robot):
    button_press_context = {
        "skill": {
            "objects": {
                "Button": "iros_button",
                "Approach": "iros_button_approach"
            },
            "approach_speed": [0.5, 1],
            "approach_acc": [1, 4],
            "press_speed": [0.24, 1],
            "press_acc": [1, 3.39],
            "duration": 0,
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0],
            "condition_level_success": "External",
            "condition_level_error": "External"
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 6, 6, 6]
            }
        },
        "user": {
            "env_X": [0.02, 0.04]
        }
    }
    # button_press_context = load_results("collective-control-001.local", "iros2021", "press_button",
    #                             "f47f43db-05c4-4b06-9da4-be092e743274", 174)
    # s = ServerProxy("http://localhost:8000", allow_none=True)
    # s.subscribe_to_event("button_press", "collective-panda-010.local", "12000")
    t = Task(robot)
    t.add_skill("button_press", "TaxPressButton", button_press_context)
    t.start()
    result = t.wait()
    print(result)


def subscribe_to_event_server(robot):
    s = ServerProxy("http://collective-control-001.local:8000", allow_none=True)
    s.subscribe_to_event("button_press", robot, "12000")


def tax_test_extraction(robot="collective-panda-008.local"):
    call_method(robot, 12000, "set_grasped_object", {"object": "generic_insertable"})
    extraction_context = {
        "skill": {
            "objects": {
                "Container": "generic_container",
                "ExtractTo": "generic_container_approach",
                "Extractable": "generic_insertable"
            },
            "extraction_speed": [0.1, 1],
            "extraction_acc": [0.5, 1],
            "search_a": [3, 1.7, 3.6, 0.64, 0.85, 0],
            "search_f": [0.77, 0, 0.8, 0.16, 0.58, 0],
            "stuck_dx_thr": 0.09
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [702, 276, 1798, 110, 131, 45]
            }
        },
        "user": {
            "env_X": [0.03, 0.08]
        }
    }
    # extraction_context = load_results("collective-control-001.local", "iros2021", "extraction",
    #                                     "6ab3f1d2-2501-4927-ac71-691340fccabd", 111)
    t = Task(robot)
    t.add_skill("extract", "TaxExtraction", extraction_context)
    t.start()
    result = t.wait()
    print(result)


def test_skill_queue(robot="localhost"):
    move1_context = {
        "skill": {
            "objects": {
                "GoalPose": "test_pose_1"
            },
            "speed": [0.1, 0.5],
            "acc": [0.5, 5]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        },
        "frames": {
            "O_R_T": [1, 0, 0, 0, 1, 0, 0, 0, 1]
        }
    }
    move2_context = {
        "skill": {
            "objects": {
                "GoalPose": "test_pose_2"
            },
            "speed": [0.1, 0.5],
            "acc": [0.5, 5]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            }
        },
        "frames": {
            "O_R_T": [1, 0, 0, 0, -1, 0, 0, 0, -1]
        }
    }
    t = Task(robot)
    t.add_skill("move1", "TaxMove", move1_context)
    t.add_skill("move2", "TaxMove", move2_context)
    t.add_skill("move3", "TaxMove", move1_context)
    t.add_skill("move4", "TaxMove", move2_context)
    t.add_skill("move5", "TaxMove", move1_context)
    t.add_skill("move6", "TaxMove", move2_context)
    t.start(True)
    result = t.wait()
    print(result)


def iros_task():
    robot = "collective-panda-010.local"

    #response = start_task(robot, "MoveToJointPose", {"pose": "iros_idle_pose"})
    #wait_for_task(robot, response["result"]["task_uuid"])
    t_0 = time.time()
    # move to grab key
    iros1 = Task(robot)

    move1_context = {
        "skill": {
            "objects": {
                "GoalPose": "iros_key_roi"
            },
            "speed": [0.7, 1],
            "acc": [2, 5]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200,200, 200]
            }
        }
    }
    grab_context = {
        "skill": {
            "objects": {
                "Retract": "iros_key_grab_retract",
                "Approach": "iros_key_grab_approach",
                "Grabbable": "iros_key"
            },
            "approach_speed": [0.5, 2],
            "approach_acc": [2, 4.0],
            "grab_speed": [0.3, 2],
            "grab_acc": [1, 4],
            "grasp_width": 0.03,
            "grasp_speed": 100,
            "grasp_force": 30,
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        }
    }
    move2_context = {
        "skill": {
            "objects": {
                "GoalPose": "iros_insertion_roi"
            },
            "speed": [0.7, 0.5],
            "acc": [2, 5]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {

                "K_x": [2000, 2000, 2000, 200,
                        200, 200]
            }
        }
    }

    insertion_context = {
        "skill": {
            "objects": {
                "Container": "iros_lock",
                "Approach": "iros_lock_approach",
                "Insertable": "iros_key"
            },
            "approach_speed": [0.5, 1],
            "approach_acc": [1, 4],
            "insertion_speed": [0.4, 0.077],
            "insertion_acc": [0.78, 1.62],
            "f_max_push": 10,
            "search_a": [5, 6, 4, 1.15, 1.5, 0],
            "search_f": [2, 1, 0.6, 0.7, 0.87, 0],
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0],
            "stuck_dx_thr": 0.035
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [1004, 536, 1617, 17, 35, 68]
            }
        },
        "user": {
            "env_X": [0.02, 0.04]
        }
    }
    turn_context = {
        "skill": {
            "objects": {
                "Turnable": "iros_key",
                "GoalOrientation": "iros_turn_goal"
            },
            "turn_speed": [0.5, 2],
            "turn_acc": [2, 25.0]},
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [665, 665, 665, 173, 173, 173]
            }
        },
        "user": {
            "env_X": [0.03, 0.04]
        }
    }
    turn_back_context = {
        "skill": {
            "objects": {
                "Turnable": "iros_key",
                "GoalOrientation": "iros_lock"
            },
            "turn_speed": [0.5, 2],
            "turn_acc": [2, 25.0]},
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [665, 665, 665, 173, 173, 173]
            }
        },
        "user": {
            "env_X": [0.03, 0.04]
        }
    }
    extraction_context = {
        "skill": {
            "objects": {
                "Container": "iros_lock",
                "ExtractTo": "iros_lock_approach",
                "Extractable": "iros_key"
            },
            "extraction_speed": [0.5, 1],
            "extraction_acc": [1, 4],
            "search_a": [0, 0, 0, 0, 0, 0],
            "search_f": [0, 0, 0, 0, 0, 0]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        },
        "user": {
            "env_X": [0.02, 0.1]
        }
    }
    move3_context = {
        "skill": {
            "objects": {
                "GoalPose": "iros_key_roi"
            },
            "speed": [0.3, 0.5],
            "acc": [1, 1]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {

                "K_x": [2000, 2000, 2000, 200,
                        200, 200]
            }
        }
    }
    place_context = {
        "skill": {
            "objects": {
                "Retract": "iros_key_grab_retract",
                "Approach": "iros_key_grab_approach",
                "Placeable": "iros_key",
                "Surface": "iros_key_storage"
            },
            "approach_speed": [0.5, 1],
            "approach_acc": [1, 4],
            "place_speed": [0.1, 0.5],
            "place_acc": [0.5, 1.0],
            "release_width": 0.03,
            "release_speed": 100,
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0]
        },
        "control": {
            "control_mode": 0
        },
        "user": {
            "env_X": [0.01, 0.02]
        }
    }
    move4_context = {
        "skill": {
            "objects": {
                "GoalPose": "iros_button_roi"
            },
            "speed": [0.5, 0.5],
            "acc": [2, 1],
            "finger_width": 0,
            "finger_speed": 100
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        }
    }
    button_press_context = {
        "skill": {
            "objects": {
                "Button": "iros_button",
                "Approach": "iros_button_approach"
            },
            "approach_speed": [0.5, 1],
            "approach_acc": [1, 4],
            "press_speed": [0.24, 1],
            "press_acc": [1, 3.39],
            "f_push": 5,
            "duration": 0,
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 150, 150, 150]
            }
        },
        "user": {
            "env_X": [0.01, 0.04]
        }
    }
    move5_context = {
        "skill": {
            "objects": {
                "GoalPose": "iros_idle_pose"
            },
            "speed": [0.3, 0.5],
            "acc": [1, 1]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        }
    }

    # iros1.add_skill("move_to_key", "TaxMove", move1_context)
    iros1.add_skill("grab_key", "TaxGrab", grab_context)
    # iros1.add_skill("move_to_insertion", "TaxMove", move2_context)
    iros1.add_skill("insertion", "TaxInsertion", insertion_context)
    iros1.add_skill("turn_key", "TaxTurn", turn_context)
    iros1.add_skill("turn_back_key", "TaxTurn", turn_back_context)
    iros1.add_skill("extraction", "TaxExtraction", extraction_context)
    # iros1.add_skill("move_to_storage", "TaxMove", move3_context)
    iros1.add_skill("place_key", "TaxPlace", place_context)
    iros1.add_skill("move_to_button", "TaxMove", move4_context)
    iros1.add_skill("press_button", "TaxPressButton", button_press_context)
    iros1.add_skill("move_to_idle", "TaxMove", move5_context)

    iros1.start(True)
    result = iros1.wait()

    print("Execution time: " + str(time.time() - t_0))

    cost = dict()

    for skill, r in result["result"]["task_result"]["skill_results"].items():
        cost[skill] = r["cost"]["time"]

    return cost


def iros_task_loop():
    cost_avg = dict()
    for i in range(1):
        cost = iros_task()
        for skill, c in cost.items():
            if skill not in cost_avg:
                cost_avg[skill] = []
            cost_avg[skill].append(c)

    with open('iros_data.csv', 'w') as f:
        write = csv.writer(f)
        write.writerow(cost_avg.keys())
        table = []
        i = 0
        for skill, c in cost_avg.items():
            table.append(c)
            i += 1

        table_np = np.asarray(table)
        table = table_np.transpose().tolist()
        write.writerows(table)
