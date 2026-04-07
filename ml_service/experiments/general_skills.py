from experiments.insertion import learn_task
from definitions.templates import ExtractionFactory, TipFactory, DragFactory, TurnLeverFactory, PressButtonFactory, BendFactory
from definitions.cost_functions import ContactForcesMetric

def learn_extraction(robot: str, extract_to: str, extractable: str, container: str, tags: list, knowledge=None,
                    wait: bool = True, n_iterations=10, service_port=8000):
    pd = ExtractionFactory(robot, ContactForcesMetric("insertion", {"contact_forces": 175}),
                           {"Extractable": extractable, "Container": container,
                            "ExtractTo": extract_to}).get_problem_definition(extractable)
    from definitions.service_configs import SVMLearner
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations, service_port=service_port)

def learn_tip(robot: str, approach: str, tippable: str, tags: list, knowledge=None,
              wait: bool = True, n_iterations=10, service_port=8000):
    pd = TipFactory(robot, ContactForcesMetric("tip", {"contact_forces": 175}),
                    {"Tippable": tippable, "Approach": approach}).get_problem_definition(tippable)
    from definitions.service_configs import SVMLearner
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations, service_port=service_port)

def learn_drag(robot: str, approach: str, draggable: str, goal_pose: str, tags: list, knowledge=None,
               wait: bool = True, n_iterations=10, service_port=8000):
    pd = DragFactory(robot, ContactForcesMetric("drag", {"contact_forces": 175}),
                     {"Draggable": draggable, "StartPose": approach, "GoalPose": goal_pose}).get_problem_definition(draggable)
    from definitions.service_configs import SVMLearner
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations, service_port=service_port)

def learn_turn_lever(robot: str, start: str, lever: str, goal: str, tags: list, knowledge=None,
                     wait: bool = True, n_iterations=10, service_port=8000):
    pd = TurnLeverFactory(robot, ContactForcesMetric("turn_lever", {"contact_forces": 175}),
                          {"Lever": lever, "StartPose": start, "GoalPosition": goal}).get_problem_definition(lever)
    from definitions.service_configs import SVMLearner
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations, service_port=service_port)

def learn_press_button(robot: str, approach: str, button: str, tags: list, knowledge=None,
                       wait: bool = True, n_iterations=10, service_port=8000):
    pd = PressButtonFactory(robot, ContactForcesMetric("press_button", {"contact_forces": 175}),
                            {"Button": button, "Approach": approach}).get_problem_definition(button)
    from definitions.service_configs import SVMLearner
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations, service_port=service_port)

def learn_bend(robot: str, start_pose: str, goal_pose: str, bendable: str, tags: list, knowledge=None,
               wait: bool = True, n_iterations=10, service_port=8000):
    pd = BendFactory(robot, ContactForcesMetric("bend", {"contact_forces": 175}),
                     {"Bendable": bendable, "StartPose": start_pose, "GoalPose": goal_pose}).get_problem_definition(bendable)
    from definitions.service_configs import SVMLearner
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations, service_port=service_port)
