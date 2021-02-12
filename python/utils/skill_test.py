#!/usr/bin/python3 -u
import time
import numpy as np

from ws_client import *


class Task:
    def __init__(self, robot):
        self.skill_names = []
        self.skill_types = []
        self.skill_context = dict()

        self.robot = robot
        self.task_uuid = "INVALID"

    def add_skill(self, name, type, context):
        self.skill_names.append(name)
        self.skill_types.append(type)
        self.skill_context[name] = context

    def start(self):
        response = start_task(self.robot, "GenericTask", parameters={
            "parameters": {
                "skill_names": self.skill_names,
                "skill_types": self.skill_types
            },
            "skills": self.skill_context
        })
        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        wait_for_task(self.robot, self.task_uuid)


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


def test_tax_grab(robot="collective-panda-008.local"):
    start_skill(robot, "TaxGrab", {"objects": {"Retract": "tax_grab_retract", "Approach": "tax_grab_approach",
                                               "Grabbable": "cylinder_60"}, "speed": [0.1, 0.5], "acc": [0.5, 1.0],
                                   "grasp_width": 0.03, "grasp_speed": 2, "grasp_force": 30,
                                   "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                                   "ROI_phi": [0, 0, 0, 0, 0, 0]}, {"control_mode": 2})


def test_tax_place(robot="collective-panda-008.local"):
    call_method(robot, 12000, "set_grasped_object", {"object": "iros_key"})
    start_skill(robot, "TaxPlace",
                {"objects": {"Retract": "iros_key_grab_retract", "Approach": "iros_key_grab_approach",
                             "Placeable": "iros_key", "Surface": "iros_key_storage"},
                 "speed": [0.05, 0.5], "acc": [0.5, 1.0],
                 "release_width": 0.06, "release_speed": 2,
                 "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                 "ROI_phi": [0, 0, 0, 0, 0, 0]}, {"control_mode": 0})


def test_tax_turn(robot="collective-panda-008.local"):
    call_method(robot, 12000, "set_grasped_object", {"object": "tax_turn_turnable"})
    start_skill(robot, "TaxTurn", {"objects": {"Turnable": "tax_turn_turnable", "GoalOrientation": "tax_turn_goal"},
                                   "turn_speed": [0.05, 0.5], "turn_acc": [0.5, 1.0]},
                {"control_mode": 0})


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
            "approach_speed": [0.2, 0.5],
            "approach_acc": [0.5, 1.0],
            "insertion_speed": [0.02, 0.5],
            "insertion_acc": [0.5, 1.0],
            "search_a": [2, 2, 0, 0, 0, 0],
            "search_f": [1, 0.75, 0, 0, 0, 0],
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
    t = Task(robot)
    t.add_skill("insertion", "TaxInsertion", insertion_context)
    t.start()


def test_tax_extraction(robot="collective-panda-008.local"):
    start_skill(robot, "TaxExtraction",
                {"objects": {"Container": "iros_lock", "ExtractTo": "iros_lock_approach",
                             "Extractable": "iros_key"}, "extraction_speed": [0.1, 0.5], "extraction_acc": [0.5, 1.0],
                 "search_a": [0, 0, 0, 0, 0, 0], "search_f": [0, 0, 0, 0, 0, 0]}, {"control_mode": 0})


def iros_task():
    robot = "collective-panda-010.local"

    response = start_task(robot, "MoveToJointPose", {"pose": "iros_idle_pose"})
    wait_for_task(robot, response["result"]["task_uuid"])
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
            "speed": [0.3, 0.5],
            "acc": [0.5, 1.0],
            "grasp_width": 0.03,
            "grasp_speed": 10,
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
            "approach_speed": [0.2, 0.5],
            "approach_acc": [0.5, 1.0],
            "insertion_speed": [0.2, 0.5],
            "insertion_acc": [0.5, 1.0],
            "search_a": [0, 0, 0, 0, 0, 0],
            "search_f": [0, 0, 0, 0, 0, 0],
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
    turn_context = {
        "skill": {
            "objects": {
                "Turnable": "iros_key",
                "GoalOrientation": "iros_turn_goal"
            },
            "turn_speed": [0.2, 3],
            "turn_acc": [0.5, 5.0]},
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        }
    }
    turn_back_context = {
        "skill": {
            "objects": {
                "Turnable": "iros_key",
                "GoalOrientation": "iros_lock"
            },
            "turn_speed": [0.2, 3],
            "turn_acc": [0.5, 5.0]},
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 200, 200, 200]
            }
        }
    }
    extraction_context = {
        "skill": {
            "objects": {
                "Container": "iros_lock",
                "ExtractTo": "iros_lock_approach",
                "Extractable": "iros_key"
            },
            "extraction_speed": [0.3, 0.5],
            "extraction_acc": [1, 1.0],
            "search_a": [0, 0, 0, 0, 0, 0],
            "search_f": [0, 0, 0, 0, 0, 0]
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000,2000, 200,200, 200]
            }
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
            "speed": [0.1, 0.5],
            "acc": [0.5, 1.0],
            "release_width": 0.03,
            "release_speed": 2,
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
    button_press_context = {
        "skill": {
            "objects": {
                "Button": "iros_button",
                "Approach": "iros_button_approach"
            },
            "approach_speed": [0.3, 0.5],
            "approach_acc": [0.5, 1.0],
            "press_speed": [0.05, 0.5],
            "press_acc": [0.5, 1.0],
            "duration": 1,
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0]
        },
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

                "K_x": [2000, 2000, 2000, 200,
                        200, 200]
            }
        }
    }

    iros1.add_skill("move_to_key", "TaxMove", move1_context)
    iros1.add_skill("grab_key", "TaxGrab", grab_context)
    iros1.add_skill("move_to_insertion", "TaxMove", move2_context)
    iros1.add_skill("insertion", "TaxInsertion", insertion_context)
    iros1.add_skill("turn_key", "TaxTurn", turn_context)
    iros1.add_skill("turn_back_key", "TaxTurn", turn_back_context)
    iros1.add_skill("extraction", "TaxExtraction", extraction_context)
    iros1.add_skill("move_to_storage", "TaxMove", move3_context)
    iros1.add_skill("place_key", "TaxPlace", place_context)
    iros1.add_skill("move_to_button", "TaxMove", move4_context)
    iros1.add_skill("press_button", "TaxPressButton", button_press_context)
    iros1.add_skill("move_to_idle", "TaxMove", move5_context)

    iros1.start()
    iros1.wait()

    print("Execution time: " + str(time.time() - t_0))
