from problem_definition.domain import Domain
from problem_definition.problem_definition import ProblemDefinition


def rastrigin():
    limits = {
        "x1": (-5.12, 5.12),
        "x2": (-5.12, 5.12),
        "x3": (-5.12, 5.12),
        "x4": (-5.12, 5.12),
        "x5": (-5.12, 5.12),
        "x6": (-5.12, 5.12)
    }
    context_mapping = {
        "x1": ["parameters.x-1"],
        "x2": ["parameters.x-2"],
        "x3": ["parameters.x-3"],
        "x4": ["parameters.x-4"],
        "x5": ["parameters.x-5"],
        "x6": ["parameters.x-6"]
    }
    domain = Domain(limits, context_mapping)
    default_context = {
        "name": "LearnerTest"
    }
    pd = ProblemDefinition("benchmark_rastrigin", domain, default_context, [], [], [], rastrigin_cost,
                           ["benchmark", "rastrigin"])
    return pd


def rastrigin_cost(cost, heuristic, success):
    return cost["ml_test"]


def insert_cylinder_30():
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
        "wiggle_a_psi": (0, 2),
        "wiggle_f_x": (0, 2),
        "wiggle_f_y": (0, 2),
        "wiggle_f_z": (0, 2),
        "wiggle_f_phi": (0, 1),
        "wiggle_f_chi": (0, 1),
        "wiggle_f_psi": (0, 1),
        "stuck_dx_thr": (0, 0.1),
        "offset_x": (-0.01, 0.01),
        "offset_y": (-0.01, 0.01),
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
        "wiggle_a_psi": ["skills.insertion.skill.search_a-6"],
        "wiggle_f_x": ["skills.insertion.skill.search_f-1"],
        "wiggle_f_y": ["skills.insertion.skill.search_f-2"],
        "wiggle_f_z": ["skills.insertion.skill.search_f-3"],
        "wiggle_f_phi": ["skills.insertion.skill.search_f-4"],
        "wiggle_f_chi": ["skills.insertion.skill.search_f-5"],
        "wiggle_f_psi": ["skills.insertion.skill.search_f-6"],
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

    domain = Domain(limits, context_mapping)
    default_context = {
        "name": "InsertObject",
        "parameters": {
            "insertable": "cylinder_30",
            "insert_into": "hole_30",
            "insert_approach": "hole_30_above",
            "offset": [0, 0, 0, 0, 0, 0]
        },
        "skills": {
            "insertion": {
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
    }
    reset_instructions = []
    task_context = {
        "name": "ExtractObject",
        "skills": {
            "extraction": {
                "skill": {
                    "traj_speed": [0.05, 0.5],
                    "traj_acc": [0.5, 1],
                    "search_a": [3, 3, 0, 2, 2, 1],
                    "search_f": [1, 0.75, 0, 1, 0.75, 0.5],
                    "stuck_dx_thr": 0.01
                }
            }
        },
        "parameters": {
            "extractable": "cylinder_30",
            "extract_from": "hole_30",
            "extract_to": "hole_30_above"
        }
    }
    reset_instructions.append({"method": "start_task", "parameters": task_context})
    pd = ProblemDefinition("insert_object", domain, default_context, [], [], reset_instructions,
                           insert_cylinder_30_cost, ["insertion", "cylinder_30"])
    return pd


def insert_cylinder_30_cost(cost, heuristic, success):
    total_cost = 0
    if "insertion" not in cost or "insertion" not in heuristic or "contact" not in cost:
        total_cost = 1000
    else:
        if success is True:
            total_cost = cost["contact"] + cost["insertion"]
    
        if success is False:
            total_cost = 10 + heuristic["insertion"]

    return total_cost
