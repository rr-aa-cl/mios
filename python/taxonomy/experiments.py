from skill_tests import *
from test_base import start_experiment


def insertion_test_cylinder_30():
    t = InsertionTest("collective-panda-008")
    start_experiment(t,
                     {"Insertable": "cylinder_30", "Container": "cylinder_30_hole", "Approach": "cylinder_30_approach"},
                     {"Extractable": "cylinder_30", "Container": "cylinder_30_hole",
                      "ExtractTo": "cylinder_30_approach", "GoalPose": "cylinder_30_approach"}, 10,
                     "114a59f4-1327-4e4d-98da-2bcc214ff926", 75)


def insertion_test_cylinder_50():
    t = InsertionTest("collective-panda-008")
    start_experiment(t,
                     {"Insertable": "cylinder_50", "Container": "cylinder_50_hole", "Approach": "cylinder_50_approach"},
                     {"Extractable": "cylinder_50", "Container": "cylinder_50_hole",
                      "ExtractTo": "cylinder_50_approach", "GoalPose": "cylinder_50_approach"}, 10,
                     "0f3ed537-2a69-401c-8476-06b0c3993b0a", 89)


def extraction_test_cylinder_30():
    t = ExtractionTest("collective-panda-008")
    start_experiment(t, {"Extractable": "cylinder_30", "Container": "cylinder_30_hole",
                         "ExtractTo": "cylinder_30_approach"},
                     {"Insertable": "cylinder_30", "Container": "cylinder_30_hole", "Approach": "cylinder_30_approach",
                      "GoalPose": "cylinder_30_approach"}, 10)


def extraction_test_cylinder_50():
    t = ExtractionTest("collective-panda-008")
    start_experiment(t, {"Extractable": "cylinder_50", "Container": "cylinder_50_hole",
                         "ExtractTo": "cylinder_50_approach"},
                     {"Insertable": "cylinder_50", "Container": "cylinder_50_hole", "Approach": "cylinder_50_approach",
                      "GoalPose": "cylinder_50_approach"}, 10)


def push_test_scale():
    t = PushTest("collective-panda-008")
    start_experiment(t, {"Surface": "push_scale", "Approach": "push_scale_approach"},
                     {"GoalPose": "push_scale_approach"}, 10)


def press_button_test_userstop():
    t = PressButtonTest("collective-panda-008")
    start_experiment(t, {"Button": "press_userstop_button", "Approach": "press_userstop_approach"},
                     {"GoalPose": "press_userstop_approach"}, 1)


def slide_object_test_mouse():
    t = SlideObjectTest("collective-panda-008")
    start_experiment(t, {"Slidable": "slide_mouse", "Surface": "slide_mouse_surface", "GoalPose": "slide_mouse_goal"},
                     {"Slidable": "slide_mouse", "GoalPose": "slide_mouse_above", "Surface": "slide_mouse_surface"}, 1)


def tip_test_enter():
    t = TipTest("collective-panda-008")
    start_experiment(t, {"Tippable": "tip_enter_key", "Approach": "tip_enter_approach"},
                     {"GoalPose": "tip_enter_approach"}, 1)


def grab_test_item():
    t = GrabTest("collective-panda-008")
    start_experiment(t, {"Approach": "grab_item_approach", "Grabbable": "grab_item", "Retract": "grab_item_retract"},
                     {"Approach": "grab_item_approach", "Placeable": "grab_item", "Retract": "grab_item_retract",
                      "Surface": "grab_item"}, 1)


def carry_test_item():
    t = CarryTest("collective-panda-008")
    start_experiment(t, {"Carriable": "carry_item", "GoalPose": "carry_item_goal"}, {"GoalPose": "carry_item_start"}, 1)


def move_test():
    t = MoveTest("collective-panda-008")
    start_experiment(t, {"GoalPose": "move_goal"}, {"GoalPose": "move_start"}, 1)


def drag_box_test():
    t = DragTest("collective-panda-008")
    start_experiment(t, {"Draggable": "drag_box", "GoalPose": "drag_box_goal"}, {}, 1)


def shove_lid_test():
    t = ShoveTest("collective-panda-008")
    start_experiment(t, {"Shovable": "shove_lid", "Approach": "shove_lid_approach", "Direction": "shove_lid_direction"},
                     {"GoalPose": "shove_lid_approach"}, 1)
