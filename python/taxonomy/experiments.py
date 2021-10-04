from skill_tests import *
from test_base import start_experiment


def insertion_test_cylinder_20():
    t = InsertionTest("collective-panda-007")
    start_experiment(t,
                     {"Insertable": "cylinder_20", "Container": "cylinder_20_hole", "Approach": "cylinder_20_approach"},
                     {"Extractable": "cylinder_20", "Container": "cylinder_20_hole",
                      "ExtractTo": "cylinder_20_approach", "GoalPose": "cylinder_20_approach"}, 50, "time")


def insertion_test_cylinder_30():
    t = InsertionTest("collective-panda-008")
    start_experiment(t,
                     {"Insertable": "cylinder_30", "Container": "cylinder_30_hole", "Approach": "cylinder_30_approach"},
                     {"Extractable": "cylinder_30", "Container": "cylinder_30_hole",
                      "ExtractTo": "cylinder_30_approach", "GoalPose": "cylinder_30_approach"}, 50, "time")


def insertion_test_cylinder_50():
    t = InsertionTest("collective-panda-008")
    start_experiment(t,
                     {"Insertable": "cylinder_50", "Container": "cylinder_50_hole", "Approach": "cylinder_50_approach"},
                     {"Extractable": "cylinder_50", "Container": "cylinder_50_hole",
                      "ExtractTo": "cylinder_50_approach", "GoalPose": "cylinder_50_approach"}, 10,
                     "0f3ed537-2a69-401c-8476-06b0c3993b0a", 89)


def insertion_test_abus_e30():
    t = InsertionTest("collective-panda-002")
    start_experiment(t,
                     {"Insertable": "key_abus_e30", "Container": "lock_abus_e30", "Approach": "lock_abus_e30_approach"},
                     {"Extractable": "key_abus_e30", "Container": "lock_abus_e30",
                      "ExtractTo": "lock_abus_e30_approach", "GoalPose": "lock_abus_e30_approach"}, 50, "time")


def extraction_test_cylinder_20():
    t = ExtractionTest("collective-panda-007")
    start_experiment(t, {"Extractable": "cylinder_20", "Container": "cylinder_20_hole",
                         "ExtractTo": "cylinder_20_approach"},
                     {"Insertable": "cylinder_20", "Container": "cylinder_20_hole", "Approach": "cylinder_20_approach",
                      "GoalPose": "cylinder_20_approach"}, 50, "time")


def extraction_test_cylinder_30():
    t = ExtractionTest("collective-panda-008")
    start_experiment(t, {"Extractable": "cylinder_30", "Container": "cylinder_30_hole",
                         "ExtractTo": "cylinder_30_approach"},
                     {"Insertable": "cylinder_30", "Container": "cylinder_30_hole", "Approach": "cylinder_30_approach",
                      "GoalPose": "cylinder_30_approach"}, 50, "time")


def extraction_test_cylinder_50():
    t = ExtractionTest("collective-panda-008")
    start_experiment(t, {"Extractable": "cylinder_50", "Container": "cylinder_50_hole",
                         "ExtractTo": "cylinder_50_approach"},
                     {"Insertable": "cylinder_50", "Container": "cylinder_50_hole", "Approach": "cylinder_50_approach",
                      "GoalPose": "cylinder_50_approach"}, 10)


def extraction_test_key_abus_e30():
    t = ExtractionTest("collective-panda-002")
    start_experiment(t, {"Extractable": "key_abus_e30", "Container": "lock_abus_e30",
                         "ExtractTo": "lock_abus_e30_approach"},
                     {"Insertable": "key_abus_e30", "Container": "lock_abus_e30", "Approach": "lock_abus_e30_approach",
                      "GoalPose": "lock_abus_e30_approach"}, 50, "time")


def push_surface_test_scale():
    t = PushSurfaceTest("collective-panda-008")
    start_experiment(t, {"Surface": "push_scale", "Approach": "push_scale_approach"},
                     {"GoalPose": "push_scale_approach"}, 50, "desired_force")


def press_button_test_userstop():
    t = PressButtonTest("collective-panda-008")
    start_experiment(t, {"Button": "press_userstop_button", "Approach": "press_userstop_approach"},
                     {"GoalPose": "press_userstop_approach"}, 50, "time")


def press_button_test_enter():
    t = PressButtonTest("collective-panda-008")
    start_experiment(t, {"Button": "tip_enter", "Approach": "tip_enter_approach"},
                     {"GoalPose": "tip_enter_approach"}, 50, "time")


def slide_object_test_mouse():
    t = SlideObjectTest("collective-panda-008")
    start_experiment(t, {"Slidable": "mouse", "Surface": "paper", "GoalPose": "slide_goal"},
                     {"Slidable": "mouse", "GoalPose": "paper", "Surface": "paper"},
                     50, "time")


def tip_test_enter():
    t = TipTest("collective-panda-008")
    start_experiment(t, {"Tippable": "tip_enter", "Approach": "tip_enter_approach"},
                     {"GoalPose": "tip_enter_approach"}, 50, "time")


def grab_test_item():
    t = GrabTest("collective-panda-008")
    start_experiment(t, {"Approach": "grab_item_approach", "Grabbable": "grab_item", "Retract": "grab_item_retract"},
                     {"Approach": "grab_item_retract", "Placeable": "grab_item", "Retract": "grab_item_approach",
                      "Surface": "grab_item"}, 50, "time")


def place_test_item():
    t = PlaceTest("collective-panda-008")
    start_experiment(t, {"Approach": "grab_item_retract", "Placeable": "grab_item", "Retract": "grab_item_approach",
                         "Surface": "grab_item"},
                     {"Approach": "grab_item_approach", "Grabbable": "grab_item", "Retract": "grab_item_retract"},
                     50, "time")


def slide_open_test():
    t = SlideOpenTest("collective-panda-008")
    start_experiment(t, {"Approach": "slide_open_approach", "Container": "slide_open_lid",
                         "GoalPose": "slide_open_goal"}, {"Approach": "slide_open_approach"}, 50, "time")


def carry_test_item():
    t = CarryTest("collective-panda-008")
    start_experiment(t, {"Carriable": "carry_item", "GoalPose": "carry_item_goal"}, {"GoalPose": "carry_item_start"}, 1)


def move_test():
    t = MoveTest("collective-panda-008")
    start_experiment(t, {"GoalPose": "move_goal"}, {"GoalPose": "move_start"}, 1)


def turn_key_test():
    t = TurnTest("collective-panda-008")
    start_experiment(t, {"Turnable": "task_board_key", "GoalOrientation": "turn_key_goal"},
                     {"Turnable": "task_board_key", "GoalOrientation": "turn_key_start"}, 50, "time")

def drag_box_test():
    t = DragTest("collective-panda-008")
    start_experiment(t, {"Draggable": "blue_box", "GoalPose": "slide_goal"}, {"GoalPose": "drag_start"}, 50, "time")


def shove_tape_test():
    t = ShoveTest("collective-panda-008")
    start_experiment(t, {"Shovable": "shove_tape", "Approach": "shove_tape_approach", "Direction": "shove_tape_direction"},
                     {"GoalPose": "shove_tape_approach"}, 50, "time")


def swipe_phone_test():
    t = SwipeTest("collective-panda-008")
    start_experiment(t, {"Stylus": "swipe_stylus", "Approach": "swipe_approach", "SwipeStart": "swipe_start",
                         "SwipeEnd": "swipe_end", "Retract": "swipe_retract"},
                     {"Stylus": "swipe_stylus", "Approach": "swipe_retract", "SwipeStart": "swipe_end",
                      "SwipeEnd": "swipe_start", "Retract": "swipe_approach"}, 50, "time")
