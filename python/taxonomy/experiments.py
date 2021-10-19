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
                      "ExtractTo": "cylinder_30_approach", "GoalPose": "cylinder_30_approach"}, 50, "time",
                     "collective-control-001", "skill_data", "cylinder_30")


def insertion_test_cylinder_30_contact():
    t = InsertionTest("collective-panda-008")
    start_experiment(t,
                     {"Insertable": "cylinder_30", "Container": "cylinder_30_hole", "Approach": "cylinder_30_approach"},
                     {"Extractable": "cylinder_30", "Container": "cylinder_30_hole",
                      "ExtractTo": "cylinder_30_approach", "GoalPose": "cylinder_30_approach"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "cylinder_30")


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
                      "ExtractTo": "lock_abus_e30_approach", "GoalPose": "lock_abus_e30_approach"}, 50, "time",
                     "collective-control-001", "skill_data", "key_abus_e30")


def insertion_test_abus_e30_contact():
    t = InsertionTest("collective-panda-002")
    start_experiment(t,
                     {"Insertable": "key_abus_e30", "Container": "lock_abus_e30", "Approach": "lock_abus_e30_approach"},
                     {"Extractable": "key_abus_e30", "Container": "lock_abus_e30",
                      "ExtractTo": "lock_abus_e30_approach", "GoalPose": "lock_abus_e30_approach"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "key_abus_e30")


def insertion_test_eth_plug():
    t = InsertionTest("collective-panda-002")
    start_experiment(t,
                     {"Insertable": "eth_plug", "Container": "eth_plug_container", "Approach": "eth_plug_approach"},
                     {"Extractable": "eth_plug", "Container": "eth_plug_container",
                      "ExtractTo": "eth_plug_approach", "GoalPose": "eth_plug_approach"}, 50, "time",
                     "collective-control-001", "skill_data", "key_abus_e30")


def insertion_test_eth_plug_contact():
    t = InsertionTest("collective-panda-002")
    start_experiment(t,
                     {"Insertable": "eth_plug", "Container": "eth_plug_container", "Approach": "eth_plug_approach"},
                     {"Extractable": "eth_plug", "Container": "eth_plug_container",
                      "ExtractTo": "eth_plug_approach", "GoalPose": "eth_plug_approach"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "key_abus_e30")


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
                      "GoalPose": "cylinder_30_approach"}, 50, "time",
                     "collective-control-001", "skill_data", "cylinder_30")


def extraction_test_cylinder_30_contact():
    t = ExtractionTest("collective-panda-008")
    start_experiment(t, {"Extractable": "cylinder_30", "Container": "cylinder_30_hole",
                         "ExtractTo": "cylinder_30_approach"},
                     {"Insertable": "cylinder_30", "Container": "cylinder_30_hole",
                      "Approach": "cylinder_30_approach",
                      "GoalPose": "cylinder_30_approach"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "cylinder_30")


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
                     {"GoalPose": "push_scale_approach"}, 50, "desired_force", "collective-control-001", "skill_data",
                     "scale")


def press_button_test_pedal():
    t = PressButtonTest("collective-panda-007")
    start_experiment(t, {"Button": "button", "Approach": "button_approach"},
                     {"GoalPose": "button_approach"}, 50, "contact_forces", "collective-control-001", "skill_data",
                     "pedal")


def press_button_test_enter():
    t = PressButtonTest("collective-panda-008")
    start_experiment(t, {"Button": "tip_enter", "Approach": "tip_enter_approach"},
                     {"GoalPose": "tip_enter_approach"}, 50, "time")


def slide_object_test_mouse():
    t = SlideObjectTest("collective-panda-008")
    start_experiment(t, {"Slidable": "mouse", "Surface": "paper", "GoalPose": "slide_goal"},
                     {"Slidable": "mouse", "GoalPose": "paper", "Surface": "paper"},
                     50, "contact_forces", "collective-control-001", "skill_data", "mouse")


def tip_test_enter():
    t = TipTest("collective-panda-007")
    start_experiment(t, {"Tippable": "enter_key", "Approach": "enter_key_approach"},
                     {"GoalPose": "enter_key_approach"}, 50, "time",
                     "collective-control-001", "skill_data", "enter_key")


def tip_test_enter_contact():
    t = TipTest("collective-panda-007")
    start_experiment(t, {"Tippable": "enter_key", "Approach": "enter_key_approach"},
                     {"GoalPose": "enter_key_approach"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "enter_key")


def grab_test_item():
    t = GrabTest("collective-panda-008")
    start_experiment(t, {"Approach": "grab_item_approach", "Grabbable": "grab_item", "Retract": "grab_item_retract"},
                     {"Approach": "grab_item_retract", "Placeable": "grab_item", "Retract": "grab_item_approach",
                      "Surface": "grab_item"}, 50, "time", "collective-control-001", "skill_data", "item")


def place_test_item():
    t = PlaceTest("collective-panda-008")
    start_experiment(t, {"Approach": "grab_item_retract", "Placeable": "grab_item", "Retract": "grab_item_approach",
                         "Surface": "grab_item"},
                     {"Approach": "grab_item_approach", "Grabbable": "grab_item", "Retract": "grab_item_retract"},
                     50, "time", "collective-control-001", "skill_data", "item")


def slide_open_test():
    t = SlideOpenTest("collective-panda-008")
    start_experiment(t, {"Approach": "slide_open_approach", "Container": "slide_open_lid",
                         "GoalPose": "slide_open_goal"}, {"Approach": "slide_open_approach"}, 50, "time",
                     "collective-control-001", "skill_data", "battery_case")


def carry_test_item():
    t = CarryTest("collective-panda-008")
    start_experiment(t, {"Carriable": "carry_item", "GoalPose": "carry_item_goal"}, {"GoalPose": "carry_item_start"}, 1)


def move_test():
    t = MoveTest("collective-panda-008")
    start_experiment(t, {"GoalPose": "move_goal"}, {"GoalPose": "move_start"}, 50, "time", "collective-control-001",
                     "skill_data", "move")


def turn_key_test():
    t = TurnTest("collective-panda-008")
    start_experiment(t, {"Turnable": "task_board_key", "GoalOrientation": "turn_key_goal"},
                     {"Turnable": "task_board_key", "GoalOrientation": "turn_key_start"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "key")

def drag_box_test():
    t = DragTest("collective-panda-008")
    start_experiment(t, {"Draggable": "blue_box", "GoalPose": "drag_goal"}, {"GoalPose": "drag_start"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "blue_box")


def shove_tape_test():
    t = ShoveTest("collective-panda-008")
    start_experiment(t, {"Shovable": "shove_tape", "Approach": "shove_tape_approach", "Direction": "shove_tape_direction"},
                     {"GoalPose": "shove_tape_approach"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "tape")


def swipe_phone_test():
    t = SwipeTest("collective-panda-008")
    start_experiment(t, {"Stylus": "swipe_stylus", "Approach": "swipe_approach", "SwipeStart": "swipe_start",
                         "SwipeEnd": "swipe_end", "Retract": "swipe_retract"},
                     {"Stylus": "swipe_stylus", "Approach": "swipe_retract", "SwipeStart": "swipe_end",
                      "SwipeEnd": "swipe_start", "Retract": "swipe_approach"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "phone")


def turn_lever_test():
    t = TurnLeverTest("collective-panda-007")
    start_experiment(t, {"Lever": "red_lever", "StartPose": "turn_lever_start", "GoalPosition": "turn_lever_goal"},
                     {"Lever": "red_lever", "StartPose": "turn_lever_goal", "GoalPosition": "turn_lever_start"}, 50,
                     "time", "collective-control-001", "skill_data", "red_lever")


def turn_lever_test_contact():
    t = TurnLeverTest("collective-panda-007")
    start_experiment(t, {"Lever": "red_lever", "StartPose": "turn_lever_start", "GoalPosition": "turn_lever_goal"},
                     {"Lever": "red_lever", "StartPose": "turn_lever_goal", "GoalPosition": "turn_lever_start"}, 50,
                     "contact_forces", "collective-control-001", "skill_data", "red_lever")


def cut_paper_test():
    t = CutTest("collective-panda-008")
    start_experiment(t, {"Knife": "cutter_knife", "Approach": "cut_approach", "CutStart": "cut_start",
                         "CutEnd": "cut_end", "Retract": "cut_retract"},
                     {"Approach": "cut_approach"}, 50, "contact_forces",
                     "collective-control-001", "skill_data", "paper")


def screw_user_stop_test():
    t = ScrewTest("collective-panda-009")
    t.reset({"Approach": "screw_approach"})
    start_experiment(t, {"Screwdriver": "screwdriver", "Approach": "screw_approach", "Screw": "screw_user_stop"},
                     {"Approach": "screw_approach"}, 1, "time",
                     "collective-control-001", "skill_data", "screw_user_stop")


def screw_out_user_stop_test():
    t = ScrewOutTest("collective-panda-009")
    t.reset({"Retract": "screw_out_retract"})
    start_experiment(t, {"Screwdriver": "screwdriver", "Approach": "screw_out_approach", "Screw": "screw_out_user_stop",
                         "GoalPosition": "screw_out_goal"},
                     {"Retract": "screw_out_retract"}, 1, "time",
                     "collective-control-001", "skill_data", "screw_out_user_stop")


def bend_test():
    t = BendTest("collective-panda-002")
    start_experiment(t, {"Bendable": "wood", "GoalPose": "bend_goal"},
                     {"Bendable": "wood", "GoalPose": "bend_start"}, 50,
                     "time", "collective-control-001", "skill_data", "wood")


def bend_test_contact():
    t = BendTest("collective-panda-002")
    start_experiment(t, {"Bendable": "wood", "GoalPose": "bend_goal"},
                     {"Bendable": "wood", "GoalPose": "bend_start"}, 50,
                     "contact_forces", "collective-control-001", "skill_data", "wood")
