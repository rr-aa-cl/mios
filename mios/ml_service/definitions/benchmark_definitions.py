from problem_definition.domain import Domain
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.problem_definition import CostFunction


def mios_ml_benchmark(x0) -> ProblemDefinition:
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
    non_shareables = ["x1"]
    domain = Domain(limits, context_mapping, non_shareables=non_shareables)
    default_context = {
        "name": "LearnerTest",
        "skills": {
            "ml_test": {
                "skill": {
                    "A": 10,
                    "x_0": [x0, x0, x0, x0, x0, x0]
                }
            }
        }
    }
    pd = ProblemDefinition("benchmark_rastrigin", domain, default_context, [], [], [], mios_ml_benchmark_cost(),
                           ["benchmark", "rastrigin", "shift_" + str(x0)])
    return pd


def mios_ml_benchmark_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("ml_test")
    c.optimum_weights[1] = 1
    c.optimum_weights[2] = 0
    c.max_cost[0] = 0
    c.max_cost[1] = 157
    c.max_cost[2] = 157
    c.finish_thr = 3
    c.geometry_factor = 1
    return c


def mios_complex_ml_benchmark(x0: list, a: float) -> ProblemDefinition:
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
        "name": "LearnerTest",
        "skills": {
            "ml_test": {
                "skill": {
                    "A": a,
                    "x_0": x0
                }
            }
        }
    }
    pd = ProblemDefinition("benchmark_rastrigin", domain, default_context, [], [], [], mios_ml_benchmark_cost(), x0,
                           tags=["benchmark", "rastrigin"])
    return pd


def mios_complex_ml_benchmark_cost() -> CostFunction:
    c = CostFunction()
    c.optimum_skills.append("ml_test")
    c.optimum_weights[1] = 0
    c.optimum_weights[2] = 1
    c.max_cost[0] = 0
    c.max_cost[1] = 157
    c.max_cost[2] = 157
    c.finish_thr = 3
    c.geometry_factor = 1
    return c