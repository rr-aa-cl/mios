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


def insertion_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("contact")
    c.optimum_skills.append("insertion")
    c.optimum_weights[0] = 1

    c.heuristic_skills = ["insertion"]
    c.max_cost[0] = 10
    c.max_cost[1] = 50
    c.finish_thr = 2
    c.geometry_factor = 0.002
    return c