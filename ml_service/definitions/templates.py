from problem_definition.domain import Domain
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.problem_definition import CostFunction


def insertion(insertable: str, insert_into: str, approach: str) -> ProblemDefinition:
    limits = {
        "speed_t": (0, 0.2),
        "speed_r": (0, 0.5),
        "acc_t": (0, 0.5),
        "acc_r": (0, 1),
        "wiggle_a_x": (0, 5),
        "wiggle_a_y": (0, 5),
        "wiggle_a_z": (0, 5),
        "wiggle_a_phi": (0, 2),
        "wiggle_a_chi": (0, 2),
        # "wiggle_a_psi": (0, 2),
        "wiggle_f_x": (0, 3),
        "wiggle_f_y": (0, 3),
        "wiggle_f_z": (0, 3),
        "wiggle_f_phi": (0, 1),
        "wiggle_f_chi": (0, 1),
        # "wiggle_f_psi": (0, 1),
        "stuck_dx_thr": (0, 0.1),
        "offset_x": (-0.005, 0.005),
        "offset_y": (-0.005, 0.005),
        "offset_phi": (-10, 10),
        "offset_chi": (-10, 10),
        "K_x": (0, 2000),
        "K_y": (0, 2000),
        "K_z": (0, 2000),
        "K_phi": (0, 200),
        "K_chi": (0, 200),
        "K_psi": (0, 200)
    }
    context_mapping = {
        "speed_t": ["skills.insertion.skill.traj_speed-1", "skills.contact.skill.speed"],
        "speed_r": ["skills.insertion.skill.traj_speed-2"],
        "acc_t": ["skills.insertion.skill.traj_acc-1"],
        "acc_r": ["skills.insertion.skill.traj_acc-2"],
        "wiggle_a_x": ["skills.insertion.skill.search_a-1"],
        "wiggle_a_y": ["skills.insertion.skill.search_a-2"],
        "wiggle_a_z": ["skills.insertion.skill.search_a-3"],
        "wiggle_a_phi": ["skills.insertion.skill.search_a-4"],
        "wiggle_a_chi": ["skills.insertion.skill.search_a-5"],
        # "wiggle_a_psi": ["skills.insertion.skill.search_a-6"],
        "wiggle_f_x": ["skills.insertion.skill.search_f-1"],
        "wiggle_f_y": ["skills.insertion.skill.search_f-2"],
        "wiggle_f_z": ["skills.insertion.skill.search_f-3"],
        "wiggle_f_phi": ["skills.insertion.skill.search_f-4"],
        "wiggle_f_chi": ["skills.insertion.skill.search_f-5"],
        # "wiggle_f_psi": ["skills.insertion.skill.search_f-6"],
        "stuck_dx_thr": ["skills.insertion.skill.stuck_dx_thr"],
        "offset_x": ["parameters.offset-1"],
        "offset_y": ["parameters.offset-2"],
        "offset_phi": ["parameters.offset-4"],
        "offset_chi": ["parameters.offset-5"],
        "K_x": ["skills.insertion.control.cart_imp.K_x-1"],
        "K_y": ["skills.insertion.control.cart_imp.K_x-2"],
        "K_z": ["skills.insertion.control.cart_imp.K_x-3"],
        "K_phi": ["skills.insertion.control.cart_imp.K_x-4"],
        "K_chi": ["skills.insertion.control.cart_imp.K_x-5"],
        "K_psi": ["skills.insertion.control.cart_imp.K_x-6"]
    }

    x_0 = {
        "speed_t": 0.2,
        "speed_r": 0.2,
        "acc_t": 0.2,
        "acc_r": 0.2,
        "wiggle_a_x": 0.2,
        "wiggle_a_y": 0.2,
        "wiggle_a_z": 0.2,
        "wiggle_a_phi": 0.2,
        "wiggle_a_chi": 0.2,
        # "wiggle_a_psi": 0.2,
        "wiggle_f_x": 0.2,
        "wiggle_f_y": 0.2,
        "wiggle_f_z": 0.2,
        "wiggle_f_phi": 0.2,
        "wiggle_f_chi": 0.2,
        # "wiggle_f_psi": 0.2,
        "stuck_dx_thr": 0.2,
        "offset_x": 0.5,
        "offset_y": 0.5,
        "offset_phi": 0.5,
        "offset_chi": 0.5,
        "K_x": 0.2,
        "K_y": 0.2,
        "K_z": 0.2,
        "K_phi": 0.2,
        "K_chi": 0.2,
        "K_psi": 0.2
    }

    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "InsertObject",
        "parameters": {
            "insertable": insertable,
            "insert_into": insert_into,
            "insert_approach": approach,
            "offset": [0, 0, 0, 0, 0, 0]
        },
        "skills": {
            "insertion": {
                "skill": {
                    "time_max": 5.0,
                    "ROI_x": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "search_f": [0, 0, 0, 0, 0, 0],
                    "search_a": [0, 0, 0, 0, 0, 0]
                }
            },
            "contact": {
                "skill": {
                    "time_max": 5.0
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "ExtractObject",
        "skills": {
            "extraction": {
                "skill": {
                    "traj_speed": [0.075, 0.5],
                    "traj_acc": [0.5, 1],
                    "search_a": [10, 10, 0, 5, 5, 1],
                    "search_f": [2, 1.5, 0, 1, 0.75, 0.5],
                    "stuck_dx_thr": 0.01
                }
            }
        },
        "parameters": {
            "extractable": insertable,
            "extract_from": insert_into,
            "extract_to": approach
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("insert_object", domain, default_context, [], [], reset_instructions,
                           insertion_cost(), ["insertion", insertable])
    return pd


def insertion_light(insertable: str, insert_into: str, approach: str) -> ProblemDefinition:
    limits = {
        "speed_t": (0, 0.2),
        "speed_r": (0, 0.5),
        "acc_t": (0, 0.5),
        "acc_r": (0, 1),
        "wiggle_a_x": (0, 5),
        "wiggle_a_phi": (0, 2),
        "wiggle_f_x": (0, 3),
        "wiggle_f_y": (0, 3),
        "wiggle_f_phi": (0, 1),
        "wiggle_f_chi": (0, 1),
        "stuck_dx_thr": (0, 0.1),
        "offset_x": (-0.005, 0.005),
        "offset_y": (-0.005, 0.005),
        "offset_phi": (-10, 10),
        "offset_chi": (-10, 10),
        "K_x": (0, 2000),
        "K_phi": (0, 200),
    }
    context_mapping = {
        "speed_t": ["skills.insertion.skill.traj_speed-1", "skills.contact.skill.speed"],
        "speed_r": ["skills.insertion.skill.traj_speed-2"],
        "acc_t": ["skills.insertion.skill.traj_acc-1"],
        "acc_r": ["skills.insertion.skill.traj_acc-2"],
        "wiggle_a_x": ["skills.insertion.skill.search_a-1", "skills.insertion.skill.search_a-2"],
        "wiggle_a_phi": ["skills.insertion.skill.search_a-4", "skills.insertion.skill.search_a-5"],
        "wiggle_f_x": ["skills.insertion.skill.search_f-1"],
        "wiggle_f_y": ["skills.insertion.skill.search_f-2"],
        "wiggle_f_phi": ["skills.insertion.skill.search_f-4"],
        "wiggle_f_chi": ["skills.insertion.skill.search_f-5"],
        "stuck_dx_thr": ["skills.insertion.skill.stuck_dx_thr"],
        "offset_x": ["parameters.offset-1"],
        "offset_y": ["parameters.offset-2"],
        "offset_phi": ["parameters.offset-4"],
        "offset_chi": ["parameters.offset-5"],
        "K_x": ["skills.insertion.control.cart_imp.K_x-1", "skills.insertion.control.cart_imp.K_x-2", "skills.insertion.control.cart_imp.K_x-3"],
        "K_phi": ["skills.insertion.control.cart_imp.K_x-4", "skills.insertion.control.cart_imp.K_x-5", "skills.insertion.control.cart_imp.K_x-6"]
    }

    x_0 = {
        "speed_t": 0.0,
        "speed_r": 0.0,
        "acc_t": 0.0,
        "acc_r": 0.0,
        "wiggle_a_x": 0.0,
        "wiggle_a_phi": 0.0,
        "wiggle_f_x": 0.0,
        "wiggle_f_y": 0.0,
        "wiggle_f_phi": 0.0,
        "wiggle_f_chi": 0.0,
        "stuck_dx_thr": 0.0,
        "offset_x": 0.5,
        "offset_y": 0.5,
        "offset_phi": 0.5,
        "offset_chi": 0.5,
        "K_x": 0.0,
        "K_phi": 0.0
    }

    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "InsertObject",
        "parameters": {
            "insertable": insertable,
            "insert_into": insert_into,
            "insert_approach": approach,
            "offset": [0, 0, 0, 0, 0, 0]
        },
        "skills": {
            "insertion": {
                "skill": {
                    "time_max": 5.0,
                    "ROI_x": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "search_f": [0, 0, 0, 0, 0, 0],
                    "search_a": [0, 0, 0, 0, 0, 0]
                },
                "control": {
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "contact": {
                "skill": {
                    "time_max": 5.0
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "ExtractObject",
        "skills": {
            "extraction": {
                "skill": {
                    "traj_speed": [0.075, 0.5],
                    "traj_acc": [0.5, 1],
                    "search_a": [10, 10, 0, 5, 5, 1],
                    "search_f": [2, 1.5, 0, 1, 0.75, 0.5],
                    "stuck_dx_thr": 0.01
                }
            }
        },
        "parameters": {
            "extractable": insertable,
            "extract_from": insert_into,
            "extract_to": approach
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("insert_object", domain, default_context, [], [], reset_instructions,
                           insertion_cost(), ["insertion", insertable])
    return pd


def insertion_demo(insertable: str, insert_into: str, approach: str) -> ProblemDefinition:
    limits = {
        "speed_t": (0.05, 0.2),
        "speed_r": (0.05, 0.5),
        "wiggle_a": (0, 5),
        "offset_x": (-0.005, 0.005),
        "offset_y": (-0.005, 0.005),
        "offset_phi": (-10, 10),
        "offset_chi": (-10, 10),
        "K_x": (300, 2000),
        "K_phi": (30, 200),
    }
    context_mapping = {
        "speed_t": ["skills.insertion.skill.traj_speed-1", "skills.contact.skill.speed"],
        "speed_r": ["skills.insertion.skill.traj_speed-2"],
        "wiggle_a": ["skills.insertion.skill.search_a-1", "skills.insertion.skill.search_a-2"],
        "offset_x": ["parameters.offset-1"],
        "offset_y": ["parameters.offset-2"],
        "offset_phi": ["parameters.offset-4"],
        "offset_chi": ["parameters.offset-5"],
        "K_x": ["skills.insertion.control.cart_imp.K_x-1", "skills.insertion.control.cart_imp.K_x-2", "skills.insertion.control.cart_imp.K_x-3"],
        "K_phi": ["skills.insertion.control.cart_imp.K_x-4", "skills.insertion.control.cart_imp.K_x-5", "skills.insertion.control.cart_imp.K_x-6"]
    }

    x_0 = {
        "speed_t": 0.0,
        "speed_r": 0.0,
        "wiggle_a": 0.0,
        "offset_x": 0.5,
        "offset_y": 0.5,
        "offset_phi": 0.5,
        "offset_chi": 0.5,
        "K_x": 0.0,
        "K_phi": 0.0
    }

    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "InsertObject",
        "parameters": {
            "insertable": insertable,
            "insert_into": insert_into,
            "insert_approach": approach,
            "offset": [0, 0, 0, 0, 0, 0]
        },
        "skills": {
            "insertion": {
                "skill": {
                    "time_max": 5.0,
                    "ROI_x": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "search_f": [1, 0.75, 0, 0, 0, 0],
                    "search_a": [0, 0, 0, 0, 0, 0],
                    "traj_acc" : [0.5, 1]
                },
                "control": {
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                }
            },
            "contact": {
                "skill": {
                    "time_max": 5.0
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "ExtractObject",
        "skills": {
            "extraction": {
                "skill": {
                    "traj_speed": [0.075, 0.5],
                    "traj_acc": [0.5, 1],
                    "search_a": [10, 10, 0, 5, 5, 1],
                    "search_f": [2, 1.5, 0, 1, 0.75, 0.5],
                    "stuck_dx_thr": 0.01
                }
            }
        },
        "parameters": {
            "extractable": insertable,
            "extract_from": insert_into,
            "extract_to": approach
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("insert_object", domain, default_context, [], [], reset_instructions,
                           insertion_cost(), ["insertion", insertable])
    return pd


def insertion_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("contact")
    c.optimum_skills.append("insertion")
    c.optimum_weights[0] = 1
    c.heuristic_expressions = "np.exp(var*100)"

    c.heuristic_skills = ["insertion"]
    c.max_cost[0] = 10
    c.max_cost[1] = 50
    c.max_cost[2] = 160
    c.finish_thr = 5
    c.geometry_factor = 0.002
    return c


def move(goal_pose: str, init_pose: str, max_time: float):
    limits = {
        "speed_t": (0, 1.7),
        "speed_r": (0, 2.5),
        "acc_t": (0, 13),
        "acc_r": (0, 25),
        "K_x": (0, 2000),
        # "K_y": (0, 2000),
        # "K_z": (0, 2000),
        "K_phi": (0, 200),
        # "K_chi": (0, 200),
        # "K_psi": (0, 200)
    }
    context_mapping = {
        "speed_t": ["skills.move.skill.speed-1"],
        "speed_r": ["skills.move.skill.speed-2"],
        "acc_t": ["skills.move.skill.acc-1"],
        "acc_r": ["skills.move.skill.acc-2"],
        "K_x": ["skills.move.control.cart_imp.K_x-1", "skills.move.control.cart_imp.K_x-2", "skills.move.control.cart_imp.K_x-3"],
        # "K_y": ["skills.move.control.cart_imp.K_x-2"],
        # "K_z": ["skills.move.control.cart_imp.K_x-3"],
        "K_phi": ["skills.move.control.cart_imp.K_x-4", "skills.move.control.cart_imp.K_x-5", "skills.move.control.cart_imp.K_x-6"],
        # "K_chi": ["skills.move.control.cart_imp.K_x-5"],
        # "K_psi": ["skills.move.control.cart_imp.K_x-6"]
    }

    x_0 = {
        "speed_t": 0.1,
        "speed_r": 0.1,
        "acc_t": 0.1,
        "acc_r": 0.1,
        "K_x": 0.1,
        # "K_y": 0.2,
        # "K_z": 0.2,
        "K_phi": 0.1,
        # "K_chi": 0.2,
        # "K_psi": 0.2
    }
    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxMove"],
            "skill_names": ["move"]
        },
        "skills": {
            "move": {
                "skill": {
                    "time_max": max_time,
                    "objects": {
                        "GoalPose": goal_pose
                    }
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                },
                "user": {
                    "env_X": [0.005, 0.025]
                }
            }
        }
    }
    reset_instructions = []
    setup_instructions = []
    task_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["MoveToPoseJoint"],
            "skill_names": ["move"]
        },
        "skills": {
            "move": {
                "skill": {
                    "speed": 0.5,
                    "acc": 1,
                    "q_g": [0, 0, 0, 0, 0, 0, 0],
                    "objects": {
                        "goal_pose": init_pose
                    }
                },
                "control": {
                    "control_mode": 3
                },
                "user": {
                    "env_X": [0.005, 0.0175]
                }
            }
        }
    }
    setup_instructions.append({"method": "start_task", "parameters": task_context})
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("move", domain, default_context, setup_instructions, [], reset_instructions,
                           move_cost(max_time), ["move"])
    return pd


def move_cost(max_time: float) -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("move")
    c.optimum_weights[0] = 1
    c.heuristic_expressions = "var"

    c.heuristic_skills = ["move"]
    c.max_cost[0] = max_time
    c.max_cost[1] = 50
    c.max_cost[2] = 160
    c.finish_thr = 5
    return c


def grab(approach_pose: str, grabbable: str, retract_pose: str, surface: str):
    limits = {
        "speed_t": (0, 0.5),
        "speed_r": (0, 1),
        "acc_t": (0, 1),
        "acc_r": (0, 4),
        "K_x": (0, 2000),
        # "K_y": (0, 2000),
        # "K_z": (0, 2000),
        "K_phi": (0, 200),
        # "K_chi": (0, 200),
        # "K_psi": (0, 200),
        "grasp_speed": (0, 10)
    }
    context_mapping = {
        "speed_t": ["skills.grab.skill.grab_speed-1"],
        "speed_r": ["skills.grab.skill.grab_speed-2"],
        "acc_t": ["skills.grab.skill.grab_acc-1"],
        "acc_r": ["skills.grab.skill.grab_acc-2"],
        "K_x": ["skills.grab.control.cart_imp.K_x-1", "skills.grab.control.cart_imp.K_x-2", "skills.grab.control.cart_imp.K_x-3"],
        # "K_y": ["skills.move.control.cart_imp.K_x-2"],
        # "K_z": ["skills.move.control.cart_imp.K_x-3"],
        "K_phi": ["skills.grab.control.cart_imp.K_x-4", "skills.grab.control.cart_imp.K_x-5", "skills.grab.control.cart_imp.K_x-6"],
        # "K_chi": ["skills.move.control.cart_imp.K_x-5"],
        # "K_psi": ["skills.move.control.cart_imp.K_x-6"]
        "grasp_speed": ["skills.grab.skill.grasp_speed"]
    }

    x_0 = {
        "speed_t": 0.1,
        "speed_r": 0.1,
        "acc_t": 0.1,
        "acc_r": 0.1,
        "K_x": 0.1,
        # "K_y": 0.2,
        # "K_z": 0.2,
        "K_phi": 0.1,
        # "K_chi": 0.2,
        # "K_psi": 0.2
        "grasp_speed": 0.1
    }
    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxGrab"],
            "skill_names": ["grab"]
        },
        "skills": {
            "grab": {
                "skill": {
                    "time_max": 5.0,
                    "grasp_width": 0.032,
                    "grasp_force": 40,
                    "approach_speed": [0.5, 1],
                    "approach_acc": [1, 4],
                    "ROI_x": [-0.3, 0.3, -0.3, 0.3, -1, 1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "objects": {
                        "Approach": approach_pose,
                        "Retract": retract_pose,
                        "Grabbable": grabbable
                    }
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxPlace"],
            "skill_names": ["place"]
        },
        "skills": {
            "place": {
                "skill": {
                    "approach_speed": [0.075, 0.5],
                    "approach_acc": [0.5, 1],
                    "place_speed": [0.075, 0.5],
                    "place_acc": [0.5, 1],
                    "release_width": 1,
                    "release_speed": 2,
                    "ROI_x": [-0.3, 0.3, -0.3, 0.3, -1, 1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "objects": {
                        "Approach": retract_pose,
                        "Retract": approach_pose,
                        "Placeable": grabbable,
                        "Surface": surface
                    }
                },
                "control": {
                    "control_mode": 2
                }
            }
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("grab", domain, default_context, [], [], reset_instructions,
                           grab_cost(), ["grab"])
    return pd


def grab_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("grab")
    c.optimum_weights[0] = 1
    c.heuristic_expressions = "var"

    c.heuristic_skills = ["grab"]
    c.max_cost[0] = 5
    c.max_cost[1] = 50
    c.max_cost[2] = 160
    c.finish_thr = 5
    return c


def place(approach_pose: str, placeable: str, retract_pose: str, surface: str):
    limits = {
        "speed_t": (0, 0.5),
        "speed_r": (0, 1),
        "acc_t": (0, 1),
        "acc_r": (0, 4),
        "K_x": (0, 2000),
        # "K_y": (0, 2000),
        # "K_z": (0, 2000),
        "K_phi": (0, 200),
        # "K_chi": (0, 200),
        # "K_psi": (0, 200)
        "release_speed": (0, 10)
    }
    context_mapping = {
        "speed_t": ["skills.place.skill.place_speed-1"],
        "speed_r": ["skills.place.skill.place_speed-2"],
        "acc_t": ["skills.place.skill.place_acc-1"],
        "acc_r": ["skills.place.skill.place_acc-2"],
        "K_x": ["skills.place.control.cart_imp.K_x-1", "skills.place.control.cart_imp.K_x-2", "skills.place.control.cart_imp.K_x-3"],
        # "K_y": ["skills.move.control.cart_imp.K_x-2"],
        # "K_z": ["skills.move.control.cart_imp.K_x-3"],
        "K_phi": ["skills.place.control.cart_imp.K_x-4", "skills.place.control.cart_imp.K_x-5", "skills.place.control.cart_imp.K_x-6"],
        # "K_chi": ["skills.move.control.cart_imp.K_x-5"],
        # "K_psi": ["skills.move.control.cart_imp.K_x-6"]
        "release_speed": ["skills.place.skill.release_speed"]
    }

    x_0 = {
        "speed_t": 0.1,
        "speed_r": 0.1,
        "acc_t": 0.1,
        "acc_r": 0.1,
        "K_x": 0.1,
        # "K_y": 0.2,
        # "K_z": 0.2,
        "K_phi": 0.1,
        # "K_chi": 0.2,
        # "K_psi": 0.2
        "release_speed": 0.1
    }
    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxPlace"],
            "skill_names": ["place"]
        },
        "skills": {
            "place": {
                "skill": {
                    "time_max": 5.0,
                    "approach_speed": [0.5, 1],
                    "approach_acc": [1, 4],
                    "release_width": 0.05,
                    "release_speed": 2,
                    "ROI_x": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "objects": {
                        "Approach": approach_pose,
                        "Retract": retract_pose,
                        "Placeable": placeable,
                        "Surface": surface
                    }
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxGrab"],
            "skill_names": ["grab"]
        },
        "skills": {
            "grab": {
                "skill": {
                    "time_max": 5.0,
                    "grasp_width": 0.032,
                    "grasp_speed": 1.6,
                    "grasp_force": 30,
                    "approach_speed": [0.5, 1],
                    "approach_acc": [1, 4],
                    "grab_speed": [0.17, 0.8],
                    "grab_acc": [0.35, 0.94],
                    "ROI_x": [-0.3, 0.3, -0.3, 0.3, -1, 1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "objects": {
                        "Approach": retract_pose,
                        "Retract": approach_pose,
                        "Grabbable": placeable
                    }
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [2000, 2000, 2000, 200, 200, 200]
                    }
                },
                "user":  {
                    "env_X": [0.01, 0.03]
                }
            }
        }
    }
    # task_context = {
    #     "name": "GenericTask",
    #     "parameters": {
    #         "skill_types": ["MoveToPoseJoint"],
    #         "skill_names": ["move"]
    #     },
    #     "skills": {
    #         "move": {
    #             "skill": {
    #                 "speed": 0.5,
    #                 "acc": 1,
    #                 "q_g": [0, 0, 0, 0, 0, 0, 0],
    #                 "objects": {
    #                     "goal_pose": approach_pose
    #                 }
    #             },
    #             "control": {
    #                 "control_mode": 3
    #             },
    #             "user": {
    #                 "env_X": [0.005, 0.0175]
    #             }
    #         }
    #     }
    # }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("place", domain, default_context, [], [], reset_instructions,
                           place_cost(), ["place"])
    return pd


def place_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("place")
    c.optimum_weights[0] = 1
    c.heuristic_expressions = "var"

    c.heuristic_skills = ["place"]
    c.max_cost[0] = 5
    c.max_cost[1] = 50
    c.max_cost[2] = 160
    c.finish_thr = 5
    return c


def press_button(approach_pose: str, button: str, init_pose: str):
    limits = {
        "press_speed_t": (0, 0.5),
        "press_speed_r": (0, 1),
        "press_acc_t": (0, 1),
        "press_acc_r": (0, 4),
        "f_push": (0, 10),
        "K_x": (0, 2000),
        # "K_y": (0, 2000),
        # "K_z": (0, 2000),
        "K_phi": (0, 200),
        # "K_chi": (0, 200),
        # "K_psi": (0, 200)
    }
    context_mapping = {
        "press_speed_t": ["skills.press_button.skill.press_speed-1"],
        "press_speed_r": ["skills.press_button.skill.press_speed-2"],
        "press_acc_t": ["skills.press_button.skill.press_acc-1"],
        "press_acc_r": ["skills.press_button.skill.press_acc-2"],
        "f_push": ["skills.press_button.skill.f_push"],
        "K_x": ["skills.press_button.control.cart_imp.K_x-1", "skills.press_button.control.cart_imp.K_x-2", "skills.press_button.control.cart_imp.K_x-3"],
        # "K_y": ["skills.move.control.cart_imp.K_x-2"],
        # "K_z": ["skills.move.control.cart_imp.K_x-3"],
        "K_phi": ["skills.press_button.control.cart_imp.K_x-4", "skills.press_button.control.cart_imp.K_x-5", "skills.press_button.control.cart_imp.K_x-6"],
        # "K_chi": ["skills.move.control.cart_imp.K_x-5"],
        # "K_psi": ["skills.move.control.cart_imp.K_x-6"]
    }

    x_0 = {
        "press_speed_t": 0.1,
        "press_speed_r": 0.1,
        "press_acc_t": 0.1,
        "press_acc_r": 0.1,
        "f_push": 0.1,
        "K_x": 0.1,
        # "K_y": 0.2,
        # "K_z": 0.2,
        "K_phi": 0.1
        # "K_chi": 0.2,
        # "K_psi": 0.2
    }
    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxPressButton"],
            "skill_names": ["press_button"]
        },
        "skills": {
            "press_button": {
                "skill": {
                    "time_max": 5.0,
                    "objects": {
                        "Approach": approach_pose,
                        "Button": button
                    },
                    "approach_speed": [0.5, 1],
                    "approach_acc": [1, 4],
                    "ROI_x": [-0.3, 0.3, -0.3, 0.3, -1, 1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "duration": 0
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["MoveToPoseJoint"],
            "skill_names": ["move"]
        },
        "skills": {
            "move": {
                "skill": {
                    "speed": 0.5,
                    "acc": 1,
                    "q_g": [0, 0, 0, 0, 0, 0, 0],
                    "objects": {
                        "goal_pose": init_pose
                    }
                },
                "control": {
                    "control_mode": 3
                },
                "user": {
                    "env_X": [0.005, 0.0175]
                }
            }
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("press_button", domain, default_context, [], [], reset_instructions,
                           press_button_cost(), ["press_button"])
    return pd


def press_button_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("press_button")
    c.optimum_weights[0] = 1
    c.heuristic_expressions = "var"

    c.heuristic_skills = ["press_button"]
    c.max_cost[0] = 5
    c.max_cost[1] = 50
    c.max_cost[2] = 160
    c.finish_thr = 5
    c.geometry_factor = 0.002
    return c


def turn(turnable: str, goal_orientation: str, initial_pose: str):
    limits = {
        "speed_r": (0, 2.5),
        "acc_r": (0, 25),
        "K_x": (0, 2000),
        # "K_y": (0, 2000),
        # "K_z": (0, 2000),
        "K_phi": (0, 200),
        # "K_chi": (0, 200),
        # "K_psi": (0, 200)
    }
    context_mapping = {
        "speed_r": ["skills.turn.skill.turn_speed-2"],
        "acc_r": ["skills.turn.skill.turn_acc-2"],
        "K_x": ["skills.turn.control.cart_imp.K_x-1", "skills.turn.control.cart_imp.K_x-2", "skills.turn.control.cart_imp.K_x-3"],
        # "K_y": ["skills.turn.control.cart_imp.K_x-2"],
        # "K_z": ["skills.turn.control.cart_imp.K_x-3"],
        "K_phi": ["skills.turn.control.cart_imp.K_x-4", "skills.turn.control.cart_imp.K_x-5", "skills.turn.control.cart_imp.K_x-6"],
        # "K_chi": ["skills.turn.control.cart_imp.K_x-5"],
        # "K_psi": ["skills.turn.control.cart_imp.K_x-6"]
    }

    x_0 = {
        "speed_r": 0.1,
        "acc_r": 0.1,
        "K_x": 0.1,
        # "K_y": 0.2,
        # "K_z": 0.2,
        "K_phi": 0.1,
        # "K_chi": 0.2,
        # "K_psi": 0.2
    }
    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_names": ["turn"],
            "skill_types": ["TaxTurn"]
        },
        "skills": {
            "turn": {
                "skill": {
                    "time_max": 5.0,
                    "turn_speed": [0.5, 0],
                    "turn_acc": [2, 0],
                    "objects": {
                        "Turnable": turnable,
                        "GoalOrientation": goal_orientation
                    }
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "GenericTask",
        "skills": {
            "turn": {
                "skill": {
                    "turn_speed": [0.075, 0.5],
                    "turn_acc": [0.5, 1],
                    "objects": {
                        "Turnable": turnable,
                        "GoalOrientation": initial_pose
                    }
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [1000, 1000, 1000, 200, 200, 200]
                    }
                },
                "user": {
                    "env_X": [0.01, 0.04]
                }
            }
        },
        "parameters": {
            "skill_names": ["turn"],
            "skill_types": ["TaxTurn"]
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("turn", domain, default_context, [], [], reset_instructions,
                           turn_cost(), ["turn"])
    return pd


def turn_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("turn")
    c.optimum_weights[0] = 1
    c.heuristic_expressions = "var"

    c.heuristic_skills = ["turn"]
    c.max_cost[0] = 5
    c.max_cost[1] = 50
    c.max_cost[2] = 160
    c.finish_thr = 5
    c.geometry_factor = 0.002
    return c


def extraction(extractable: str, container: str, extract_to: str):
    limits = {
        "speed_t": (0, 0.5),
        "speed_r": (0, 1),
        "acc_t": (0, 1),
        "acc_r": (0, 4),
        "wiggle_a_x": (0, 10),
        "wiggle_a_y": (0, 10),
        "wiggle_a_z": (0, 10),
        "wiggle_a_phi": (0, 2),
        "wiggle_a_chi": (0, 2),
        # "wiggle_a_psi": (0, 2),
        "wiggle_f_x": (0, 3),
        "wiggle_f_y": (0, 3),
        "wiggle_f_z": (0, 3),
        "wiggle_f_phi": (0, 1),
        "wiggle_f_chi": (0, 1),
        # "wiggle_f_psi": (0, 1),
        "stuck_dx_thr": (0, 0.1),
        "K_x": (0, 2000),
        "K_y": (0, 2000),
        "K_z": (0, 2000),
        "K_phi": (0, 200),
        "K_chi": (0, 200),
        "K_psi": (0, 200)
    }
    context_mapping = {
        "speed_t": ["skills.extract.skill.extraction_speed-1"],
        "speed_r": ["skills.extract.skill.extraction_speed-2"],
        "acc_t": ["skills.extract.skill.extraction_acc-1"],
        "acc_r": ["skills.extract.skill.extraction_acc-2"],
        "wiggle_a_x": ["skills.extract.skill.search_a-1"],
        "wiggle_a_y": ["skills.extract.skill.search_a-2"],
        "wiggle_a_z": ["skills.extract.skill.search_a-3"],
        "wiggle_a_phi": ["skills.extract.skill.search_a-4"],
        "wiggle_a_chi": ["skills.extract.skill.search_a-5"],
        # "wiggle_a_psi": ["skills.extract.skill.search_a-6"],
        "wiggle_f_x": ["skills.extract.skill.search_f-1"],
        "wiggle_f_y": ["skills.extract.skill.search_f-2"],
        "wiggle_f_z": ["skills.extract.skill.search_f-3"],
        "wiggle_f_phi": ["skills.extract.skill.search_f-4"],
        "wiggle_f_chi": ["skills.extract.skill.search_f-5"],
        # "wiggle_f_psi": ["skills.extract.skill.search_f-6"],
        "stuck_dx_thr": ["skills.extract.skill.stuck_dx_thr"],
        "K_x": ["skills.extract.control.cart_imp.K_x-1"],
        "K_y": ["skills.extract.control.cart_imp.K_x-2"],
        "K_z": ["skills.extract.control.cart_imp.K_x-3"],
        "K_phi": ["skills.extract.control.cart_imp.K_x-4"],
        "K_chi": ["skills.extract.control.cart_imp.K_x-5"],
        "K_psi": ["skills.extract.control.cart_imp.K_x-6"]
    }

    x_0 = {
        "speed_t": 0.1,
        "speed_r": 0.1,
        "acc_t": 0.1,
        "acc_r": 0.1,
        "wiggle_a_x": 0.1,
        "wiggle_a_y": 0.1,
        "wiggle_a_z": 0.1,
        "wiggle_a_phi": 0.1,
        "wiggle_a_chi": 0.1,
        # "wiggle_a_psi": 0.2,
        "wiggle_f_x": 0.1,
        "wiggle_f_y": 0.1,
        "wiggle_f_z": 0.1,
        "wiggle_f_phi": 0.1,
        "wiggle_f_chi": 0.1,
        # "wiggle_f_psi": 0.2,
        "stuck_dx_thr": 0.1,
        "K_x": 0.1,
        "K_y": 0.1,
        "K_z": 0.1,
        "K_phi": 0.1,
        "K_chi": 0.1,
        "K_psi": 0.1
    }
    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_names": ["extract"],
            "skill_types": ["TaxExtraction"]
        },
        "skills": {
            "extract": {
                "skill": {
                    "time_max": 5.0,
                    "objects": {
                        "Extractable": extractable,
                        "Container": container,
                        "ExtractTo": extract_to
                    }
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "GenericTask",
        "skills": {
            "extract": {
                "skill": {
                    "extraction_speed": [0.075, 0.5],
                    "extraction_acc": [0.5, 1],
                    "objects": {
                        "Extractable": extractable,
                        "Container": container,
                        "ExtractTo": extract_to
                    }
                },
                "control": {
                    "control_mode": 0
                }
            },
            "insert": {
                "skill": {
                    "approach_speed": [0.1, 0.5],
                    "approach_acc": [0.5, 1],
                    "insertion_speed": [0.05, 0.5],
                    "insertion_acc": [0.5, 1],
                    "ROI_x": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "objects": {
                        "Insertable": extractable,
                        "Container": container,
                        "Approach": extract_to
                    }
                },
                "control": {
                    "control_mode": 0
                }
            }
        },
        "parameters": {
            "skill_names": ["extract", "insert"],
            "skill_types": ["TaxExtraction", "TaxInsertion"]
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("extraction", domain, default_context, [], [], reset_instructions,
                           extraction_cost(), ["extraction", extractable])
    return pd


def extraction_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("extract")
    c.optimum_weights[0] = 1
    c.heuristic_expressions = "np.exp(var*100)"

    c.heuristic_skills = ["extract"]
    c.max_cost[0] = 5
    c.max_cost[1] = 50
    c.max_cost[2] = 160
    c.finish_thr = 5
    c.geometry_factor = 0.002
    return c


def tax_insertion(insertable: str, container: str, approach: str) -> ProblemDefinition:
    limits = {
        "speed_i_t": (0, 0.5),
        "speed_i_r": (0, 1),
        "acc_i_t": (0, 1),
        "acc_i_r": (0, 4),
        "wiggle_a_x": (0, 10),
        "wiggle_a_y": (0, 10),
        "wiggle_a_z": (0, 10),
        "wiggle_a_phi": (0, 2),
        "wiggle_a_chi": (0, 2),
        # "wiggle_a_psi": (0, 2),
        "wiggle_f_x": (0, 3),
        "wiggle_f_y": (0, 3),
        "wiggle_f_z": (0, 3),
        "wiggle_f_phi": (0, 1),
        "wiggle_f_chi": (0, 1),
        # "wiggle_f_psi": (0, 1),
        "stuck_dx_thr": (0, 0.1),
        "offset_x": (-0.005, 0.005),
        "offset_y": (-0.005, 0.005),
        "offset_phi": (-10, 10),
        "offset_chi": (-10, 10),
        "K_x": (0, 2000),
        "K_y": (0, 2000),
        "K_z": (0, 2000),
        "K_phi": (0, 200),
        "K_chi": (0, 200),
        "K_psi": (0, 200)
    }
    context_mapping = {
        "speed_i_t": ["skills.insertion.skill.insertion_speed-1"],
        "speed_i_r": ["skills.insertion.skill.insertion_speed-2"],
        "acc_i_t": ["skills.insertion.skill.insertion_acc-1"],
        "acc_i_r": ["skills.insertion.skill.insertion_acc-2"],
        "wiggle_a_x": ["skills.insertion.skill.search_a-1"],
        "wiggle_a_y": ["skills.insertion.skill.search_a-2"],
        "wiggle_a_z": ["skills.insertion.skill.search_a-3"],
        "wiggle_a_phi": ["skills.insertion.skill.search_a-4"],
        "wiggle_a_chi": ["skills.insertion.skill.search_a-5"],
        # "wiggle_a_psi": ["skills.insertion.skill.search_a-6"],
        "wiggle_f_x": ["skills.insertion.skill.search_f-1"],
        "wiggle_f_y": ["skills.insertion.skill.search_f-2"],
        "wiggle_f_z": ["skills.insertion.skill.search_f-3"],
        "wiggle_f_phi": ["skills.insertion.skill.search_f-4"],
        "wiggle_f_chi": ["skills.insertion.skill.search_f-5"],
        # "wiggle_f_psi": ["skills.insertion.skill.search_f-6"],
        "stuck_dx_thr": ["skills.insertion.skill.stuck_dx_thr"],
        "offset_x": ["skills.insertion.skill.DeltaX-1"],
        "offset_y": ["skills.insertion.skill.DeltaX-2"],
        "offset_phi": ["skills.insertion.skill.DeltaX-4"],
        "offset_chi": ["skills.insertion.skill.DeltaX-5"],
        "K_x": ["skills.insertion.control.cart_imp.K_x-1"],
        "K_y": ["skills.insertion.control.cart_imp.K_x-2"],
        "K_z": ["skills.insertion.control.cart_imp.K_x-3"],
        "K_phi": ["skills.insertion.control.cart_imp.K_x-4"],
        "K_chi": ["skills.insertion.control.cart_imp.K_x-5"],
        "K_psi": ["skills.insertion.control.cart_imp.K_x-6"]
    }

    x_0 = {
        "speed_i_t": 0.1,
        "speed_i_r": 0.1,
        "acc_i_t": 0.1,
        "acc_i_r": 0.1,
        "wiggle_a_x": 0.1,
        "wiggle_a_y": 0.1,
        "wiggle_a_z": 0.1,
        "wiggle_a_phi": 0.1,
        "wiggle_a_chi": 0.1,
        # "wiggle_a_psi": 0.1,
        "wiggle_f_x": 0.1,
        "wiggle_f_y": 0.1,
        "wiggle_f_z": 0.1,
        "wiggle_f_phi": 0.1,
        "wiggle_f_chi": 0.1,
        # "wiggle_f_psi": 0.1,
        "stuck_dx_thr": 0.1,
        "offset_x": 0.5,
        "offset_y": 0.5,
        "offset_phi": 0.5,
        "offset_chi": 0.5,
        "K_x": 0.1,
        "K_y": 0.1,
        "K_z": 0.1,
        "K_phi": 0.1,
        "K_chi": 0.1,
        "K_psi": 0.1
    }

    domain = Domain(limits, context_mapping, x_0)
    default_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxInsertion"],
            "skill_names": ["insertion"]
        },
        "skills": {
            "insertion": {
                "skill": {
                    "time_max": 5.0,
                    "ROI_x": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -1, 1],
                    "search_f": [0, 0, 0, 0, 0, 0],
                    "search_a": [0, 0, 0, 0, 0, 0],
                    "DeltaX": [0, 0, 0, 0, 0, 0],
                    "approach_speed": [0.5, 1],
                    "approach_acc": [1, 4],
                    "f_max_push": 10,
                    "objects": {
                        "Insertable": insertable,
                        "Container": container,
                        "Approach": approach,
                    }
                },
                "control": {
                    "control_mode": 0,
                    "cart_imp": {
                        "K_x": [0, 0, 0, 0, 0, 0]
                    }
                },
                "user": {
                    "env_X": [0.01, 0.03]
                }
            }
        }
    }
    reset_instructions = []
    task_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxExtraction", "TaxMove", "MoveToPoseJoint"],
            "skill_names": ["extraction", "move_up", "move"]
        },
        "skills": {
            "extraction": {
                "skill": {
                    "extraction_speed": [0.075, 0.5],
                    "extraction_acc": [0.5, 1],
                    "search_a": [0, 0, 0, 0, 0, 0],
                    "search_f": [2, 1.5, 0, 1, 0.75, 0.5],
                    "stuck_dx_thr": 0.01,
                    "objects": {
                        "Extractable": insertable,
                        "Container": container,
                        "ExtractTo": approach
                    }
                },
                "control": {
                    "control_mode": 0
                },
                "user": {
                    "env_X": [0.01, 0.03]
                }
            },
            "move_up": {
                "skill": {
                    "speed": [0.1, 0.5],
                    "acc": [0.5, 1],
                    "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0.05, 1],
                    "objects": {
                        "GoalPose": "EndEffector",
                    }
                },
                "control": {
                    "control_mode": 0
                },
                "user": {
                    "env_X": [0.01, 0.03]
                }
            },
            "move": {
                "skill": {
                    "speed": 0.5,
                    "acc": 1,
                    "q_g": [0, 0, 0, 0, 0, 0, 0],
                    "objects": {
                        "goal_pose": approach
                    }
                },
                "control": {
                    "control_mode": 3
                },
                "user": {
                    "env_X": [0.005, 0.0175]
                }
            }
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("insert_object", domain, default_context, [], [], reset_instructions,
                           tax_insertion_cost(), ["insertion", insertable])
    return pd


def tax_insertion_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("insertion")
    c.optimum_weights[0] = 1
    c.heuristic_expressions = "np.exp(var*100)"

    c.heuristic_skills = ["insertion"]
    c.max_cost[0] = 5
    c.max_cost[1] = 50
    c.max_cost[2] = 160
    c.finish_thr = 5
    c.geometry_factor = 0.002
    return c