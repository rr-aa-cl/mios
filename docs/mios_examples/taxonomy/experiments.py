from skill_tests import *
from test_base import start_experiment


def insertion_test(robot: str, insertable: str, container: str, approach: str, cf: str):
    t = InsertionTest(robot)
    start_experiment(t,
                     {"Insertable": insertable, "Container": container, "Approach": approach},
                     {"Extractable": insertable, "Container": container,
                      "ExtractTo": approach, "GoalPose": approach}, 1, cf,
                     "collective-control-001", "skill_data", insertable)


def extraction_test(robot: str, extractable: str, container: str, extract_to: str, cf: str):
    t = ExtractionTest(robot)
    start_experiment(t, {"Extractable": extractable, "Container": container,
                         "ExtractTo": extract_to},
                     {"Insertable": extractable, "Container": container,
                      "Approach": extract_to,
                      "GoalPose": extract_to}, 1, cf,
                     "collective-control-001", "skill_data", extractable)


def press_button_test(robot: str, button: str, pressed: str, approach: str, cf: str):
    t = PressButtonTest(robot)
    start_experiment(t, {"Button": button, "Approach": approach, "Pressed": pressed},
                     {"GoalPose": approach}, 1, cf, "collective-control-001", "skill_data",
                     button)


def tip_test(robot: str, tippable: str, tipped: str, approach: str, cf: str):
    t = TipTest(robot)
    start_experiment(t, {"Tippable": tippable, "Approach": approach, "Tipped": tipped},
                     {"GoalPose": approach}, 50, cf,
                     "collective-control-001", "skill_data", tippable)


def drag_test(robot: str, draggable: str, goal_pose: str, start_pose: str, cf: str):
    t = DragTest(robot)
    start_experiment(t, {"Draggable": draggable, "GoalPose": goal_pose}, {"GoalPose": start_pose}, 50, cf,
                     "collective-control-001", "skill_data", draggable)


def slide_object_test(robot: str, slidable: str, surface: str, goal_pose: str, start_pose: str, cf: str):
    t = SlideObjectTest(robot)
    start_experiment(t, {"Slidable": slidable, "Surface": surface, "GoalPose": goal_pose},
                     {"Slidable": slidable, "GoalPose": start_pose, "Surface": surface},
                     50, cf, "collective-control-001", "skill_data", surface)


def grab_test(robot: str, grabbable: str, approach: str, retract: str, cf: str):
    t = GrabTest(robot)
    start_experiment(t, {"Approach": approach, "Grabbable": grabbable, "Retract": retract},
                     {"Approach": retract, "Placeable": grabbable, "Retract": approach,
                      "Surface": grabbable}, 50, cf, "collective-control-001", "skill_data", grabbable)


def place_test(robot: str, placeable: str, approach: str, retract: str, cf: str):
    t = PlaceTest(robot)
    start_experiment(t, {"Approach": approach, "Placeable": placeable, "Retract": retract,
                         "Surface": placeable},
                     {"Approach": retract, "Grabbable": placeable, "Retract": approach},
                     50, cf, "collective-control-001", "skill_data", placeable)


def shove_test(robot: str, shovable: str, approach: str, direction: str, cf: str, surface: str):
    t = ShoveTest(robot)
    start_experiment(t, {"Shovable": shovable, "Approach": approach, "Direction": direction, "Surface": surface},
                     {"GoalPose": approach}, 50, cf,
                     "collective-control-001", "skill_data", surface)


def cut_test(robot: str, knife: str, approach: str, start: str, end: str, retract: str, cf: str, surface: str):
    t = CutTest(robot)
    start_experiment(t, {"Knife": knife, "Approach": approach, "CutStart": start,
                         "CutEnd": end, "Retract": retract, "Surface": surface},
                     {"Approach": approach}, 50, cf,
                     "collective-control-001", "skill_data", surface)


def turn_lever_test(robot: str, lever: str, start: str, goal: str, cf: str):
    t = TurnLeverTest(robot)
    start_experiment(t, {"Lever": lever, "StartPose": start, "GoalPosition": goal},
                     {"Lever": lever, "StartPose": goal, "GoalPosition": start}, 50,
                     cf, "collective-control-001", "skill_data", lever)


def bend_test(robot: str, bendable: str, goal: str, start: str, cf: str):
    t = BendTest(robot)
    start_experiment(t, {"Bendable": bendable, "GoalPose": goal},
                     {"Bendable": bendable, "GoalPose": start}, 50,
                     cf, "collective-control-001", "skill_data", bendable)


def turn_test(robot: str, turnable: str, goal: str, start: str, cf: str):
    t = TurnTest(robot)
    start_experiment(t, {"Turnable": turnable, "GoalOrientation": goal},
                     {"Turnable": turnable, "GoalOrientation": start}, 1, cf,
                     "collective-control-001", "skill_data", turnable)


def swipe_test(robot: str, stylus: str, approach: str, start: str, end: str, retract: str, surface: str, cf: str):
    t = SwipeTest(robot)
    start_experiment(t, {"Stylus": stylus, "Approach": approach, "SwipeStart": start,
                         "SwipeEnd": end, "Retract": retract},
                     {"Stylus": stylus, "Approach": retract, "SwipeStart": end,
                      "SwipeEnd": start, "Retract": approach}, 50, cf,
                     "collective-control-001", "skill_data", surface)


def slide_open_test(robot: str, container: str, approach: str, goal: str, cf: str):
    t = SlideOpenTest(robot)
    start_experiment(t, {"Approach": approach, "Container": container,
                         "GoalPose": goal}, {"Approach": approach}, 50, cf,
                     "collective-control-001", "skill_data", container)


def crank_test(robot: str, crank: str, center: str, start: str, cf: str):
    t = SlideOpenTest(robot)
    start_experiment(t, {"Crank": crank, "Center": center}, {"GoalPose": start}, 50, cf,
                     "collective-control-001", "skill_data", crank)


def push_surface_test(robot: str, surface: str, approach: str, cf: str):
    t = PushSurfaceTest(robot)
    start_experiment(t, {"Surface": surface, "Approach": approach},
                     {"GoalPose": approach}, 50, cf, "collective-control-001", "skill_data",
                     surface)


def file_test(robot: str, file: str, approach: str, start: str, end: str, retract: str, edge: str, cf: str):
    t = FileTest(robot)
    start_experiment(t, {"File": file, "Approach": approach, "FileStart": start,
                         "FileEnd": end, "Retract": retract},
                     {"File": file, "Approach": retract, "FileStart": end,
                      "FileEnd": start, "Retract": approach}, 50, cf,
                     "collective-control-001", "skill_data", edge)


def hammer_test(robot: str, hammer: str, approach: str, hammerable: str, goal: str, cf: str):
    t = HammerTest(robot)
    start_experiment(t, {"Hammer": hammer, "Approach": approach, "Hammerable": hammerable, "GoalPosition": goal},
                     {"Approach": approach}, 50, cf, "collective-control-001", "skill_data",
                     hammerable)


def wipe_test(robot: str, wiper: str, approach: str, wipeable: str, direction: str, cf: str):
    t = WipeTest(robot)
    start_experiment(t, {"Wiper": wiper, "Approach": approach, "Wipeable": wipeable, "Direction": direction},
                     {"Approach": approach}, 50, cf, "collective-control-001", "skill_data",
                     wipeable)


def carry_test_item():
    t = CarryTest("collective-panda-008")
    start_experiment(t, {"Carriable": "carry_item", "GoalPose": "carry_item_goal"}, {"GoalPose": "carry_item_start"}, 1)


def move_test():
    t = MoveTest("collective-panda-008")
    start_experiment(t, {"GoalPose": "move_goal"}, {"GoalPose": "move_start"}, 50, "time", "collective-control-001",
                     "skill_data", "move")


def screw_in_test(robot: str, screwdriver: str, approach: str, screw: str, cf: str):
    t = ScrewInTest(robot)
    t.reset({"Approach": approach})
    start_experiment(t, {"Screwdriver": screwdriver, "Approach": approach, "Screw": screw},
                     {"Approach": approach}, 1, cf,
                     "collective-control-001", "skill_data", "screw_in_user_stop")


def screw_out_user_stop_test():
    t = ScrewOutTest("collective-panda-009")
    t.reset({"Retract": "screw_out_retract"})
    start_experiment(t, {"Screwdriver": "screwdriver", "Approach": "screw_out_approach", "Screw": "screw_out_user_stop",
                         "GoalPosition": "screw_out_goal"},
                     {"Retract": "screw_out_retract"}, 1, "time",
                     "collective-control-001", "skill_data", "screw_out_user_stop")
