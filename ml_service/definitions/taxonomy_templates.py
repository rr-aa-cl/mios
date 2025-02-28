from definitions.definitions_base import *


class InsertionFactory(ProblemDefinitionFactory):

    def get_limits(self):
        limits = {
            "p0_offset_x": (-0.005, 0.005),
            "p0_offset_y": (-0.005, 0.005),
            "p0_offset_phi": (-10, 10),
            "p0_offset_chi": (-10, 10),
            "p1_dx_d": (0, 0.1),
            "p1_dphi_d": (0, 0.5),
            "p1_ddx_d": (0, 0.5),
            "p1_ddphi_d": (0, 1),
            "p1_K_x": (0, 2000),
            "p1_K_phi": (0, 2000),
            "p2_dx_d": (0, 0.1),
            "p2_dphi_d": (0, 0.5),
            "p2_ddx_d": (0, 0.5),
            "p2_ddphi_d": (0, 1),
            "p2_wiggle_a_x": (0, 10),
            "p2_wiggle_a_y": (0, 10),
            # "p2_wiggle_a_z": (0, 10),
            "p2_wiggle_a_phi": (0, 2),
            "p2_wiggle_a_chi": (0, 2),
            "p2_wiggle_f_x": (0, 3),
            "p2_wiggle_f_y": (0, 3),
            # "p2_wiggle_f_z": (0, 3),
            "p2_wiggle_f_phi": (0, 1),
            "p2_wiggle_f_chi": (0, 1),
            "p2_wiggle_phi_x": (0, 6.28),
            "p2_wiggle_phi_y": (0, 6.28),
            # "p2_wiggle_phi_z": (0, 6.28),
            "p2_wiggle_phi_phi": (0, 6.28),
            "p2_wiggle_phi_chi": (0, 6.28),
            "p2_K_x": (0, 2000),
            "p2_K_y": (0, 2000),
            "p2_K_z": (0, 2000),
            "p2_K_phi": (0, 200),
            "p2_K_chi": (0, 200),
            "p2_K_psi": (0, 200),
            "p2_f_push_x": (-10, 10),
            "p2_f_push_y": (-10, 10),
            "p2_f_push_z": (0, 15)
        }
        return limits

    def get_mapping(self):
        context_mapping = {
            "p0_offset_x": ["skills.insertion.skill.p0.DeltaX-1"],
            "p0_offset_y": ["skills.insertion.skill.p0.DeltaX-2"],
            "p0_offset_phi": ["skills.insertion.skill.p0.DeltaX-4"],
            "p0_offset_chi": ["skills.insertion.skill.p0.DeltaX-5"],
            "p1_dx_d": ["skills.insertion.skill.p1.dX_d-1"],
            "p1_dphi_d": ["skills.insertion.skill.p1.dX_d-2"],
            "p1_ddx_d": ["skills.insertion.skill.p1.ddX_d-1"],
            "p1_ddphi_d": ["skills.insertion.skill.p1.ddX_d-2"],
            "p1_K_x": ["skills.insertion.skill.p1.K_x-1", "skills.insertion.skill.p1.K_x-2",
                       "skills.insertion.skill.p1.K_x-3"],
            "p1_K_phi": ["skills.insertion.skill.p1.K_x-4", "skills.insertion.skill.p1.K_x-5",
                         "skills.insertion.skill.p1.K_x-6"],
            "p2_dx_d": ["skills.insertion.skill.p2.dX_d-1"],
            "p2_dphi_d": ["skills.insertion.skill.p2.dX_d-2"],
            "p2_ddx_d": ["skills.insertion.skill.p2.ddX_d-1"],
            "p2_ddphi_d": ["skills.insertion.skill.p2.ddX_d-2"],
            "p2_wiggle_a_x": ["skills.insertion.skill.p2.search_a-1"],
            "p2_wiggle_a_y": ["skills.insertion.skill.p2.search_a-2"],
            # "p2_wiggle_a_z": ["skills.insertion.skill.p2.search_a-3"],
            "p2_wiggle_a_phi": ["skills.insertion.skill.p2.search_a-4"],
            "p2_wiggle_a_chi": ["skills.insertion.skill.p2.search_a-5"],
            "p2_wiggle_f_x": ["skills.insertion.skill.p2.search_f-1"],
            "p2_wiggle_f_y": ["skills.insertion.skill.p2.search_f-2"],
            # "p2_wiggle_f_z": ["skills.insertion.skill.p2.search_f-3"],
            "p2_wiggle_f_phi": ["skills.insertion.skill.p2.search_f-4"],
            "p2_wiggle_f_chi": ["skills.insertion.skill.p2.search_f-5"],
            "p2_wiggle_phi_x": ["skills.insertion.skill.p2.search_phi-1"],
            "p2_wiggle_phi_y": ["skills.insertion.skill.p2.search_phi-2"],
            # "p2_wiggle_phi_z": ["skills.insertion.skill.p2.search_phi-3"],
            "p2_wiggle_phi_phi": ["skills.insertion.skill.p2.search_phi-4"],
            "p2_wiggle_phi_chi": ["skills.insertion.skill.p2.search_phi-5"],
            "p2_K_x": ["skills.insertion.skill.p2.K_x-1"],
            "p2_K_y": ["skills.insertion.skill.p2.K_x-2"],
            "p2_K_z": ["skills.insertion.skill.p2.K_x-3"],
            "p2_K_phi": ["skills.insertion.skill.p2.K_x-4"],
            "p2_K_chi": ["skills.insertion.skill.p2.K_x-5"],
            "p2_K_psi": ["skills.insertion.skill.p2.K_x-6"],
            "p2_f_push_x": ["skills.insertion.skill.p2.f_push-1"],
            "p2_f_push_y": ["skills.insertion.skill.p2.f_push-2"],
            "p2_f_push_z": ["skills.insertion.skill.p2.f_push-3"]
        }
        return context_mapping

    def get_initial_values(self):
        x_0 = dict()
        for p in self.limits:
            x_0[p] = 0.1

        x_0["p0_offset_x"] = 0.5,
        x_0["p0_offset_y"] = 0.5,
        x_0["p0_offset_phi"] = 0.5,
        x_0["p0_offset_chi"] = 0.5,
        x_0["p2_f_push_x"] = 0.5,
        x_0["p2_f_push_y"] = 0.5,
        return x_0

def insertion(objects: dict, cost_function: str, max_cost: float) -> ProblemDefinition:
    insertable = objects["Insertable"]
    container = objects["Container"]
    approach = objects["Approach"]



    ĺimits = InsertionFactory.get_limits()
    context_mapping = InsertionFactory.get_mapping()

    domain = Domain(limits, context_mapping, x_0)
    default_skill_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxInsertion"],
            "skill_names": ["insertion"]
        },
        "skills": {
            "insertion": {
                "skill": {
                    "time_max": 5.0,
                    "ROI_x": [-0.03, 0.03, -0.03, 0.03, -0.1, 0.1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -0.1, 0.1],
                    "objects": {
                        "Insertable": insertable,
                        "Container": container,
                        "Approach": approach,
                    },
                    "p0": {
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "K_x": [2000, 2000, 2000, 200, 200, 200],
                        "DeltaX": [0, 0, 0, 0, 0, 0]
                    },
                    "p1": {
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "K_x": [2000, 2000, 2000, 200, 200, 200]
                    },
                    "p2": {
                        "search_a": [0, 0, 0, 0, 0, 0],
                        "search_f": [0, 0, 0, 0, 0, 0],
                        "search_phi": [0, 0, 0, 0, 0, 0],
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "K_x": [2000, 2000, 2000, 200, 200, 200],
                        "f_push": [0, 0, 0, 0, 0, 0]
                    },
                    "p3": {
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "K_x": [2000, 2000, 2000, 200, 200, 200],
                        "f_push": 0
                    }
                },
                "control": {
                    "control_mode": 0
                },
                "user": {
                    "env_X": [0.01, 0.01, 0.001, 0.03, 0.03, 0.03]
                }
            }
        }
    }
    setup_instructions = []
    setup_context = {
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
                        "goal_pose": approach
                    }
                },
                "control": {
                    "control_mode": 3
                },
                "user": {
                    "env_X": [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175]
                }
            }
        }
    }
    reset_instructions = []
    reset_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxExtraction", "MoveToPoseJoint"],
            "skill_names": ["extraction", "move"]
        },
        "skills": {
            "extraction": {
                "skill": {
                    "objects": {
                        "Extractable": insertable,
                        "Container": container,
                        "ExtractTo": approach
                    },
                    "p0":{
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "search_a": [0, 0, 0, 0, 0, 0],
                        "search_f": [0, 0, 0, 0, 0, 0],
                        "K_x": [500, 500, 1000, 100, 100, 100]
                    },
                    "p1": {
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "K_x": [500, 500, 1000, 100, 100, 100]
                    }
                },
                "control": {
                    "control_mode": 0
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
                    "env_X": [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175]
                }
            }
        }
    }

    object_modifier = {
        "insertion": {
            "Approach": {
                "T_T_OB": {
                    "x": (-0.003, 0.003),
                    "y": (-0.003, 0.003)
                },
                "linked_objects" : ["Container"]
            }
        }
    }

    setup_instructions.append({"method": "start_task", "parameters": setup_context})
    reset_instructions.append({"method": "start_task", "parameters": reset_context})
    pd = ProblemDefinition("insertion", insertable, domain, default_skill_context, setup_instructions, [], reset_instructions,
                           insertion_cost(cost_function, max_cost), [1], tags=["insertion", insertable])
    return pd


def insertion_cost(cost_function: str, max_cost: float) -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("insertion")
    c.optimum_weights[cost_function] = 1
    c.max_cost[cost_function] = max_cost
    c.heuristic_skills = ["insertion"]
    c.heuristic_expressions = "np.exp(var)"
    return c


def tip(objects: dict, cost_function: str, max_cost: float) -> ProblemDefinition:
    tippable = objects["Tippable"]
    approach = objects["Approach"]

    limits = {
        "p1_dx_d": (0, 0.1),
        "p1_dphi_d": (0, 0.5),
        "p1_ddx_d": (0, 0.5),
        "p1_ddphi_d": (0, 1),
        "p1_K_x": (0, 2000),
        "p1_K_phi": (0, 200),
        "p1_f_tip": (0, 20),
        "p2_dx_d": (0, 0.1),
        "p2_dphi_d": (0, 0.5),
        "p2_ddx_d": (0, 0.5),
        "p2_ddphi_d": (0, 1),
        "p2_K_x": (0, 2000),
        "p2_K_phi": (0, 200)
    }
    context_mapping = {
        "p1_dx_d": ["skills.tip.skill.p1.dX_d-1"],
        "p1_dphi_d": ["skills.tip.skill.p1.dX_d-2"],
        "p1_ddx_d": ["skills.tip.skill.p1.ddX_d-1"],
        "p1_ddphi_d": ["skills.tip.skill.p1.ddX_d-2"],
        "p1_K_x": ["skills.tip.skill.p1.K_x-1", "skills.tip.skill.p1.K_x-2",
                   "skills.tip.skill.p1.K_x-3"],
        "p1_K_phi": ["skills.tip.skill.p1.K_x-4", "skills.tip.skill.p1.K_x-5",
                     "skills.tip.skill.p1.K_x-6"],
        "p1_f_tip": ["skills.tip.skill.p1.f_tip-1"],
        "p2_dx_d": ["skills.tip.skill.p2.dX_d-1"],
        "p2_dphi_d": ["skills.tip.skill.p2.dX_d-2"],
        "p2_ddx_d": ["skills.tip.skill.p2.ddX_d-1"],
        "p2_ddphi_d": ["skills.tip.skill.p2.ddX_d-2"],
        "p2_K_x": ["skills.tip.skill.p2.K_x-1", "skills.tip.skill.p2.K_x-2",
                   "skills.tip.skill.p2.K_x-3"],
        "p2_K_phi": ["skills.tip.skill.p2.K_x-4", "skills.tip.skill.p2.K_x-5",
                     "skills.tip.skill.p2.K_x-6"]
    }
    x_0 = dict()
    for p in limits:
        x_0[p] = 0.1

    domain = Domain(limits, context_mapping, x_0)
    default_skill_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxTip"],
            "skill_names": ["tip"]
        },
        "skills": {
            "insertion": {
                "skill": {
                    "time_max": 5.0,
                    "ROI_x": [-0.03, 0.03, -0.03, 0.03, -0.1, 0.1],
                    "ROI_phi": [-0.03, 0.03, -0.03, 0.03, -0.1, 0.1],
                    "objects": {
                        "Tippable": tippable,
                        "Approach": approach
                    },
                    "p0": {
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "K_x": [2000, 2000, 2000, 200, 200, 200],
                    },
                    "p1": {
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "K_x": [2000, 2000, 2000, 200, 200, 200],
                        "f_tip": 0
                    },
                    "p2": {
                        "dX_d": [0.1, 0.5],
                        "ddX_d": [0.5, 1],
                        "K_x": [2000, 2000, 2000, 200, 200, 200],
                    }
                },
                "control": {
                    "control_mode": 0
                },
                "user": {
                    "env_X": [0.005, 0.005, 0.005, 0.03, 0.03, 0.03]
                }
            }
        }
    }
    setup_instructions = []
    setup_context = {
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
                        "goal_pose": approach
                    }
                },
                "control": {
                    "control_mode": 3
                },
                "user": {
                    "env_X": [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175]
                }
            }
        }
    }
    reset_instructions = []
    reset_context = {
        "name": "GenericTask",
        "parameters": {
            "skill_types": ["TaxExtraction", "MoveToPoseJoint"],
            "skill_names": ["extraction", "move"]
        },
        "skills": {
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
                    "env_X": [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175]
                }
            }
        }
    }

    object_modifier = {
        "insertion": {
            "Approach": {
                "T_T_OB": {
                    "x": (-0.003, 0.003),
                    "y": (-0.003, 0.003)
                },
                "linked_objects" : ["Tippable"]
            }
        }
    }

    setup_instructions.append({"method": "start_task", "parameters": setup_context})
    reset_instructions.append({"method": "start_task", "parameters": reset_context})
    pd = ProblemDefinition("tip", tippable, domain, default_skill_context, setup_instructions, [], reset_instructions,
                           tip_cost(cost_function, max_cost), [1], tags=["tip", tippable])

    return pd


def tip_cost(cost_function: str, max_cost: float) -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("tip")
    c.optimum_weights[cost_function] = 1
    c.max_cost[cost_function] = max_cost
    c.heuristic_skills = ["tip"]
    c.heuristic_expressions = "np.exp(var)"
    return c