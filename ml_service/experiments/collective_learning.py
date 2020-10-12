from task_scheduler.task_scheduler import Task
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from task_scheduler.creation_pipeline import CreationPipeline
from services.cmaes import CMAESConfiguration
from definitions import insert_cylinder_30
from utils.udp_client import call_method
from experiments.experiment_base import Experiment
import copy
import random


def insert_cylinder_10():
    pd = insert_cylinder_30()
    pd.default_context["parameters"]["insertable"] = "cylinder_10"
    pd.default_context["parameters"]["insert_into"] = "hole_10"
    pd.default_context["parameters"]["insert_approach"] = "hole_10_above"
    pd.default_context["skills"]["insertion"]["skill"]["ROI_x"] = [-0.01, 0.01, -0.01, 0.01, -1, 1]
    pd.reset_instructions[0]["parameters"]["parameters"]["extractable"] = "cylinder_10"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_from"] = "hole_10"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_to"] = "hole_10_above"
    pd.tags = ["cylinder_10"]
    return pd


def insert_cylinder_20():
    pd = insert_cylinder_30()
    pd.default_context["parameters"]["insertable"] = "cylinder_20"
    pd.default_context["parameters"]["insert_into"] = "hole_20"
    pd.default_context["parameters"]["insert_approach"] = "hole_20_above"
    pd.default_context["skills"]["insertion"]["skill"]["ROI_x"] = [-0.02, 0.02, -0.02, 0.02, -1, 1]
    pd.reset_instructions[0]["parameters"]["parameters"]["extractable"] = "cylinder_20"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_from"] = "hole_20"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_to"] = "hole_20_above"
    pd.tags = ["cylinder_20"]
    return pd


def insert_cylinder_40():
    pd = insert_cylinder_30()
    pd.default_context["parameters"]["insertable"] = "cylinder_40"
    pd.default_context["parameters"]["insert_into"] = "hole_40"
    pd.default_context["parameters"]["insert_approach"] = "hole_40_above"
    pd.default_context["skills"]["insertion"]["skill"]["ROI_x"] = [-0.04, 0.04, -0.04, 0.04, -1, 1]
    pd.reset_instructions[0]["parameters"]["parameters"]["extractable"] = "cylinder_40"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_from"] = "hole_40"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_to"] = "hole_40_above"
    pd.tags = ["cylinder_40"]
    return pd


def insert_cylinder_50():
    pd = insert_cylinder_30()
    pd.default_context["parameters"]["insertable"] = "cylinder_50"
    pd.default_context["parameters"]["insert_into"] = "hole_50"
    pd.default_context["parameters"]["insert_approach"] = "hole_50_above"
    pd.default_context["skills"]["insertion"]["skill"]["ROI_x"] = [-0.05, 0.05, -0.05, 0.05, -1, 1]
    pd.reset_instructions[0]["parameters"]["parameters"]["extractable"] = "cylinder_50"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_from"] = "hole_50"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_to"] = "hole_50_above"
    pd.tags = ["cylinder_50"]
    return pd


def insert_cylinder_60():
    pd = insert_cylinder_30()
    pd.default_context["parameters"]["insertable"] = "cylinder_60"
    pd.default_context["parameters"]["insert_into"] = "hole_60"
    pd.default_context["parameters"]["insert_approach"] = "hole_60_above"
    pd.default_context["skills"]["insertion"]["skill"]["ROI_x"] = [-0.06, 0.06, -0.06, 0.06, -1, 1]
    pd.reset_instructions[0]["parameters"]["parameters"]["extractable"] = "cylinder_60"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_from"] = "hole_60"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_to"] = "hole_60_above"
    pd.tags = ["cylinder_60"]
    return pd


def insert_key_abus():
    pd = insert_cylinder_30()
    pd.default_context["parameters"]["insertable"] = "key_abus_e30"
    pd.default_context["parameters"]["insert_into"] = "lock_abus_e30"
    pd.default_context["parameters"]["insert_approach"] = "lock_abus_e30_above"
    pd.default_context["skills"]["insertion"]["skill"]["ROI_x"] = [-0.01, 0.01, -0.01, 0.01, -1, 1]
    pd.reset_instructions[0]["parameters"]["parameters"]["extractable"] = "key_abus_e30"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_from"] = "lock_abus_e30"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_to"] = "lock_abus_e30_above"
    pd.tags = ["key_abus_e30"]
    return pd


def insert_plug_usb_c():
    pd = insert_cylinder_30()
    pd.default_context["parameters"]["insertable"] = "plug_usb_c"
    pd.default_context["parameters"]["insert_into"] = "slot_usb_c"
    pd.default_context["parameters"]["insert_approach"] = "slot_usb_c_above"
    pd.default_context["skills"]["insertion"]["skill"]["ROI_x"] = [-0.01, 0.01, -0.01, 0.01, -1, 1]
    pd.reset_instructions[0]["parameters"]["parameters"]["extractable"] = "plug_usb_c"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_from"] = "slot_usb_c"
    pd.reset_instructions[0]["parameters"]["parameters"]["extract_to"] = "slot_usb_c_above"
    pd.tags = ["plug_usb_c"]
    return pd


class TestCreationPipeline(CreationPipeline):
    def __init__(self):
        super().__init__()

    def create_tasks_from_template(self, template: ProblemDefinition, service_configuration: ServiceConfiguration,
                                   n_tasks, service_url, agents, knowledge_mode: str):
        for i in range(n_tasks):
            t = Task(copy.deepcopy(template), service_configuration, agents, service_url, knowledge_mode)
            t.problem_definition.cost_function.optimum_weights[0] = float(i + 1) / float(n_tasks)
            t.problem_definition.cost_function.optimum_weights[1] = 1 - \
                                                                    t.problem_definition.cost_function.optimum_weights[
                                                                        0]
            self.tasks.append(t)

        random.shuffle(self.tasks)


class CollectiveLearningBase(Experiment):
    def initialize(self, knowledge_mode: str):
        config = CMAESConfiguration()
        config.n_gen = 10
        config.n_ind = 10

        call_method("collective-panda-001.local", 12002, "set_grasped_object", {"object": "cylinder_40"})
        call_method("collective-panda-002.local", 12002, "set_grasped_object", {"object": "key_abus_e30"})
        call_method("collective-panda-007.local", 12002, "set_grasped_object", {"object": "cylinder_10"})
        call_method("collective-panda-008.local", 12002, "set_grasped_object", {"object": "cylinder_60"})
        call_method("collective-panda-009.local", 12002, "set_grasped_object", {"object": "plug_usb_c"})

        c = TestCreationPipeline()
        n_tasks = 10
        c.create_tasks_from_template(insert_cylinder_10(), config, n_tasks, "collective-panda-007.local",
                                     ["collective-panda-007"], knowledge_mode)
        c.create_tasks_from_template(insert_cylinder_40(), config, n_tasks, "collective-panda-001.local",
                                     ["collective-panda-001"], knowledge_mode)
        c.create_tasks_from_template(insert_cylinder_60(), config, n_tasks, "collective-panda-008.local",
                                     ["collective-panda-008"], knowledge_mode)
        c.create_tasks_from_template(insert_key_abus(), config, n_tasks, "collective-panda-002.local",
                                     ["collective-panda-002"], knowledge_mode)
        c.create_tasks_from_template(insert_plug_usb_c(), config, n_tasks, "collective-panda-009.local",
                                     ["collective-panda-009"], knowledge_mode)

        self.insert_creation_pipeline(c)
