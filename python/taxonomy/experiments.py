from skill_tests import *
from test_base import start_experiment


def insertion_test_cylinder_30():
    t = InsertionTest("collective-panda-008")
    start_experiment(t,
                     {"Insertable": "cylinder_30", "Container": "cylinder_30_hole", "Approach": "cylinder_30_approach"},
                     {"Extractable": "cylinder_30", "Container": "cylinder_30_hole",
                      "ExtractTo": "cylinder_30_approach", "GoalPose": "cylinder_30_approach"}, 10,
                     "0f3ed537-2a69-401c-8476-06b0c3993b0a", 89)


def insertion_test_cylinder_50():
    t = InsertionTest("collective-panda-008")
    start_experiment(t,
                     {"Insertable": "cylinder_50", "Container": "cylinder_50_hole", "Approach": "cylinder_50_approach"},
                     {"Extractable": "cylinder_50", "Container": "cylinder_50_hole",
                      "ExtractTo": "cylinder_50_approach", "GoalPose": "cylinder_50_approach"}, 1,
                     "0f3ed537-2a69-401c-8476-06b0c3993b0a", 89)


def extraction_test_cylinder_30():
    t = ExtractionTest("collective-panda-008")
    start_experiment(t, {"Extractable": "cylinder_30", "Container": "cylinder_30_hole",
                         "ExtractTo": "cylinder_30_approach"},
                     {"Insertable": "cylinder_30", "Container": "cylinder_30_hole", "Approach": "cylinder_30_approach",
                      "GoalPose": "cylinder_30_approach"}, 10, "0f3ed537-2a69-401c-8476-06b0c3993b0a", 89)


def extraction_test_cylinder_50():
    t = ExtractionTest("collective-panda-008")
    start_experiment(t, {"Extractable": "cylinder_50", "Container": "cylinder_50_hole",
                         "ExtractTo": "cylinder_50_approach"},
                     {"Insertable": "cylinder_50", "Container": "cylinder_50_hole", "Approach": "cylinder_50_approach",
                      "GoalPose": "cylinder_50_approach"}, 10, "0f3ed537-2a69-401c-8476-06b0c3993b0a", 89)
