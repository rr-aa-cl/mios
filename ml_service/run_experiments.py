from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *
from utils.experiment_wizard import start_experiment
from utils.taxonomy_utils import *
import os


def learn_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 10, keep_record: bool = False, knowledge = None, wait: bool = False):
    start_experiment(robot, [robot], problem_definition, service_config, 10, knowledge=knowledge, tags=tags,
                     keep_record=False, wait=wait)


def test_learning():
    pd = InsertionFactory("collective-panda-001", ContactForcesMetric("insertion", {"contact_forces": 175}),
                          {"Insertable": "cylinder_40", "Container": "cylinder_40_container",
                           "Approach": "cylinder_40_container_approach"}).get_problem_definition("cylinder_40")
    sc = SVMLearner().get_configuration()
    learn_task("collective-panda-001", pd, sc, ["test_learning"])


def learn_insertion(robot: str, approach: str, insertable: str, container: str, tags: list, knowledge=None,
                    wait: bool=True):
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                          {"Insertable": insertable, "Container": container,
                           "Approach": approach}).get_problem_definition(insertable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge)


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

def transfer_video_grab_insertable(robot: str, insertable: str, container: str, approach: str, above: str):
    # call_method(robot, 12000, "release_object")
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t1 = Task(robot)
    t2 = Task(robot)
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = above
    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = insertable

    f = open(path_to_default_context + "extraction.json")
    extraction_context = json.load(f)
    extraction_context["skill"]["objects"]["Extractable"] = insertable
    extraction_context["skill"]["objects"]["Container"] = container
    extraction_context["skill"]["objects"]["ExtractTo"] = approach

    t1.add_skill("move", "MoveToPoseJoint", move_context)
    t1.add_skill("move_fine", "TaxMove", move_fine_context)
    t1.start()
    t1.wait()
    call_method(robot, 12000, "grasp_object", {"object": insertable})
    t2.add_skill("extraction", "TaxExtraction", extraction_context)
    t2.start()
    t2.wait()


def transfer_video_place_insertable(robot: str, insertable: str, container: str, approach: str, above: str):
    # call_method(robot, 12000, "grasp_object", {"object": insertable})
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t1 = Task(robot)
    t2 = Task(robot)

    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    insertion_context["skill"]["objects"]["Insertable"] = insertable
    insertion_context["skill"]["objects"]["Container"] = container
    insertion_context["skill"]["objects"]["Approach"] = approach

    insertion_context["skill"]["p2"]["search_a"]= [10, 10, 0, 2, 2, 0]
    insertion_context["skill"]["p2"]["search_f"] = [1, 0.75, 0, 1, 0.75, 0]
    insertion_context["skill"]["p2"]["f_push"] = [0, 0, 20, 0, 0, 0]

    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = above
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = above
    t1.add_skill("insertion", "TaxInsertion", insertion_context)
    t1.start()
    t1.wait()
    call_method(robot, 12000, "release_object")
    t2.add_skill("move_fine", "TaxMove", move_fine_context)
    t2.add_skill("move", "MoveToPoseJoint", move_context)
    t2.start()
    t2.wait()


def transfer_video(robot: str):
    insertables = ["key_old", "key_hatch", "key_pad", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40",
                   "cylinder_50", "cylinder_60"]
    containers = ["lock_old", "lock_hatch", "lock_pad", "container_10", "container_20", "container_30", "container_40",
                   "container_50", "container_60"]
    approaches = ["lock_old_approach", "lock_hatch_approach", "lock_pad_approach", "container_10_approach", "container_20_approach", "container_30_approach", "container_40_approach",
                   "container_50_approach", "container_60_approach"]
    aboves = ["lock_old_above", "lock_hatch_above", "lock_pad_above", "container_10_above",
                   "container_20_above", "container_30_above", "container_40_above",
                   "container_50_above", "container_60_above"]

    # knowledge = None
    insertables.reverse()
    containers.reverse()
    approaches.reverse()
    aboves.reverse()
    for i in range(len(insertables)):
        if i == 0:
            knowledge = None
        else:
            knowledge = {"type": "similar", "mode": "specific", "kb_location": "collective-panda-008",
                         "kb_db": "ml_results", "kb_task_type": "insertion", "scope":
                             ["insertion", "cylinder_40", "n1", "video_prior"]}
        transfer_video_grab_insertable(robot, insertables[i], containers[i], approaches[i], aboves[i])
        learn_insertixon(robot, approaches[i], insertables[i], containers[i], ["transfer_video"],
                       knowledge , wait=False)
        s = ServerProxy("http://" + robot + ":8000", allow_none=True)
        input("Press Enter to stop learning.")
        s.stop_service()
        while s.is_busy() is True:
            time.sleep(1)
        input("Press Enter to continue")
        transfer_video_place_insertable(robot, insertables[i], containers[i], approaches[i], aboves[i])