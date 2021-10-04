from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *
from utils.experiment_wizard import start_experiment


def learn_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 10, keep_record: bool = False):
    start_experiment(robot, [robot], problem_definition, service_config, 10, tags=tags, keep_record=False)


def test_learning():
    pd = InsertionFactory("collective-panda-001", ContactForcesMetric("insertion", {"contact_forces": 60}),
                          {"Insertable": "cylinder_40", "Container": "cylinder_40_container",
                           "Approach": "cylinder_40_container_approach"}).get_problem_definition("cylinder_40")
    sc = SVMLearner().get_configuration()
    learn_task("collective-panda-001", pd, sc, ["test_learning"])


def learn_insertion(robot: str, approach: str, insertable: str, container: str, tags: list):
    pd = InsertionFactory(robot, ContactForcesMetric("insertion", {"contact_forces": 60}),
                          {"Insertable": insertable, "Container": container,
                           "Approach": approach}).get_problem_definition(insertable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)


def learn_tip(robot: str, approach: str, tippable: str, tags: list):
    pd = TipFactory(robot, ContactForcesMetric("tip", {"contact_forces": 60}),
                          {"Tippable": tippable, "Approach": approach}).get_problem_definition(tippable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)
