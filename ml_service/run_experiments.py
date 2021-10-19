from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *
from utils.experiment_wizard import start_experiment


def learn_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 10, keep_record: bool = False):
    start_experiment(robot, [robot], problem_definition, service_config, 10, tags=tags, keep_record=False)


def test_learning():
    pd = InsertionFactory("collective-panda-001", ContactForcesMetric("insertion", {"contact_forces": 175}),
                          {"Insertable": "cylinder_40", "Container": "cylinder_40_container",
                           "Approach": "cylinder_40_container_approach"}).get_problem_definition("cylinder_40")
    sc = SVMLearner().get_configuration()
    learn_task("collective-panda-001", pd, sc, ["test_learning"])


def learn_insertion(robot: str, approach: str, insertable: str, container: str, tags: list):
    pd = InsertionFactory(robot, ContactForcesMetric("insertion", {"contact_forces": 175}),
                          {"Insertable": insertable, "Container": container,
                           "Approach": approach}).get_problem_definition(insertable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)


def learn_extraction(robot: str, extract_to: str, extractable: str, container: str, tags: list):
    pd = ExtractionFactory(robot, ContactForcesMetric("insertion", {"contact_forces": 175}),
                          {"Extractable": extractable, "Container": container,
                           "ExtractTo": extract_to}).get_problem_definition(extractable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)


def learn_tip(robot: str, approach: str, tippable: str, tags: list):
    pd = TipFactory(robot, ContactForcesMetric("tip", {"contact_forces": 175}),
                          {"Tippable": tippable, "Approach": approach}).get_problem_definition(tippable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)


def learn_drag(robot: str, approach: str, draggable: str, goal_pose: str, tags: list):
    pd = DragFactory(robot, ContactForcesMetric("drag", {"contact_forces": 175}),
                          {"Draggable": draggable, "StartPose": approach, "GoalPose": goal_pose}).get_problem_definition(draggable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)


def learn_turn_lever(robot: str, start: str, lever: str, goal: str, tags: list):
    pd = TurnLeverFactory(robot, ContactForcesMetric("turn_lever", {"contact_forces": 175}),
                          {"Lever": lever, "StartPose": start, "GoalPosition": goal}).get_problem_definition(lever)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)


def learn_press_button(robot: str, approach: str, button: str, tags: list):
    pd = PressButtonFactory(robot, ContactForcesMetric("press_button", {"contact_forces": 175}),
                          {"Button": button, "Approach": approach}).get_problem_definition(button)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)


def learn_bend(robot: str, start_pose: str, goal_pose: str, bendable: str, tags: list):
    pd = BendFactory(robot, ContactForcesMetric("bend", {"contact_forces": 175}),
                          {"Bendable": bendable, "StartPose": start_pose, "GoalPose": goal_pose}).get_problem_definition(bendable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags)
