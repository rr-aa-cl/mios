#!/usr/bin/python3 -u
import time
import numpy as np

from ws_client import *
from xmlrpc.client import ServerProxy

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
        print(self.task_uuid)
        return result


def test_insertion(robot, insertable, container, approach):
    call_method(robot, 12000, "set_grasped_object", {"object": insertable})
    context = {
        "skill": {
            "objects": {
                "Container": container,
                "Approach": approach,
                "Insertable": insertable
            },
            "time_max": 10,
            "p0": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "DeltaX": [0, 0, 0, 0, 10, 0],
                "K_x":[1000, 1000, 1000, 100, 100, 100]
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
            "p2": {
                "search_a": [10, 10, 0, 0, 0, 0],
                "search_f": [1, 0.75, 0, 0, 0, 0],
                "K_x": [200, 200, 0, 100, 100, 100],
                "f_push": 10
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "f_push": 10,
                "K_x": [1000, 1000, 0, 100, 100, 100]
            }
        },
        "control": {
            "control_mode": 0
        },
        "user": {
            "env_dX": [0.01, 0.05]
        }
    }
    t = Task(robot)
    t.add_skill("insertion", "TaxInsertion", context)
    t.start()
    result = t.wait()
    print(result)


def test_extraction(robot, extractable, container, retreat):
    call_method(robot, 12000, "set_grasped_object", {"object": extractable})
    context = {
        "skill": {
            "objects": {
                "Container": container,
                "ExtractTo": retreat,
                "Extractable": extractable
            },
            "time_max": 10,
            "p0": {
                "search_a": [5, 5, 0, 1, 1, 0],
                "search_f": [2, 1.5, 0, 1, 0.75, 0],
                "K_x": [50, 50, 1000, 50, 50, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
                #"f_pull": 40
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                #"f_pull": 40,
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            }
        },
        "control": {
            "control_mode": 0
        },
        "user": {
            "env_dX": [0.01, 0.05]
        }
    }
    t = Task(robot)
    t.add_skill("extraction", "TaxExtraction", context)
    t.start()
    result = t.wait()
    print(result)


def test_push(robot, surface, approach):
    context = {
        "skill": {
            "objects": {
                "Surface": surface,
                "Approach": approach
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
            "p2": {
                "duration": 5,
                "f_push": 5,
                "K_x": [1000, 1000, 0, 100, 100, 100]
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("push", "TaxPush", context)
    t.start()
    result = t.wait()
    print(result)


def test_pull(robot, pullable):
    call_method(robot, 12000, "set_grasped_object", {"object": pullable})
    context = {
        "skill": {
            "objects": {
                "Pullable": pullable
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 0, 100, 100, 100],
                "f_pull": 10,
                "duration": 5
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("pull", "TaxPull", context)
    t.start()
    result = t.wait()
    print(result)


def test_press_button(robot, button, approach):
    context = {
        "skill": {
            "objects": {
                "Button": button,
                "Approach": approach
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
            "p2": {
                "duration": 5,
                "f_push": 40,
                "K_x": [1000, 1000, 0, 100, 100, 100]
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("press_button", "TaxPressButton", context)
    t.start()
    result = t.wait()
    print(result)


def test_tip(robot, tippable, approach):
    context = {
        "skill": {
            "objects": {
                "Tippable": tippable,
                "Approach": approach
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "f_tip": 10
            },
            "p2": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("tip", "TaxTip", context)
    t.start()
    result = t.wait()
    print(result)


def test_grab(robot, approach, grabbable, retract):
    context = {
        "skill": {
            "objects": {
                "Grabbable": grabbable,
                "Approach": approach,
                "Retract": retract
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "gripper_speed": 0.2,
                "gripper_width": 0.06
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
            "p2": {
                "grasp_width": 0.03,
                "grasp_speed": 0.2,
                "grasp_force": 40,
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("grab", "TaxGrab", context)
    t.start()
    result = t.wait()
    print(result)


def test_place(robot, approach, placeable, surface, retract):
    call_method(robot, 12000, "set_grasped_object", {"object": placeable})
    context = {
        "skill": {
            "objects": {
                "Placeable": placeable,
                "Approach": approach,
                "Retract": retract,
                "Surface": surface
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
            "p2": {
                "release_width": 0.06,
                "release_speed": 0.2,
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            },
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("place", "TaxPlace", context)
    t.start()
    result = t.wait()
    print(result)


def test_shove(robot, approach, shovable, location):
    context = {
        "skill": {
            "objects": {
                "Shovable": shovable,
                "Approach": approach,
                "Location": location,
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1000, 100, 100, 100]
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("shove", "TaxShove", context)
    t.start()
    result = t.wait()
    print(result)


def test_turn_lever(robot, lever, goal_position):
    call_method(robot, 12000, "set_grasped_object", {"object": lever})
    context = {
        "skill": {
            "objects": {
                "Lever": lever,
                "GoalPosition": goal_position
            },
            "time_max": 10,
            "p0": {
                "K_x": [500, 1000, 500, 50, 50, 50],
                "dX_d": [0.05, 0.5],
                "ddX_d": [0.5, 1],
            }
        },
        "user": {
            "env_X": [0.01, 1]
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("turn_lever", "TaxTurnLever", context)
    t.start()
    result = t.wait()
    print(result)


def test_move(robot, goal_pose):
    context = {
        "skill": {
            "objects": {
                "GoalPose": goal_pose
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "finger_width": -1,
                "finger_speed": -1,
                "t_settle": 0.5,
                "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("move", "TaxMove", context)
    t.start()
    result = t.wait()
    print(result)


def test_carry(robot, goal_pose, carriable):
    call_method(robot, 12000, "set_grasped_object", {"object": carriable})
    context = {
        "skill": {
            "objects": {
                "GoalPose": goal_pose,
                "Carriable": carriable
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("carry", "TaxCarry", context)
    t.start()
    result = t.wait()
    print(result)


def test_slide(robot, goal_pose, slidable, surface):
    call_method(robot, 12000, "set_grasped_object", {"object": slidable})
    context = {
        "skill": {
            "objects": {
                "GoalPose": goal_pose,
                "Slidable": slidable,
                "Surface": surface
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 0, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "f_slide": 10
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("slide", "TaxSlide", context)
    t.start()
    result = t.wait()
    print(result)


def test_swipe(robot, approach, swipe_start, swipe_end, retract, stylus):
    call_method(robot, 12000, "set_grasped_object", {"object": stylus})
    context = {
        "skill": {
            "objects": {
                "Approach": approach,
                "SwipeStart": swipe_start,
                "SwipeEnd": swipe_end,
                "Retract": retract,
                "Stylus": stylus
            },
            "time_max": 10,
            "p0": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p1": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p2": {
                "K_x": [1000, 1000, 0, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "f_swipe": 10
            },
            "p3": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("swipe", "TaxSwipe", context)
    t.start()
    result = t.wait()
    print(result)