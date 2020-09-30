from task_scheduler.creation_pipeline import CreationPipeline
from services.cmaes import CMAESConfiguration
from task_scheduler.task_scheduler import TaskScheduler
from task_scheduler.task_scheduler import Task
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from definitions import rastrigin
import copy


class TestCreationPipeline(CreationPipeline):
    def __init__(self):
        super().__init__()

    def create_tasks_from_template(self, template: ProblemDefinition, service_configuration: ServiceConfiguration, n_tasks, service_url, agents, knowledge_mode: str):
        for i in range(n_tasks):
            t = Task(copy.deepcopy(template), service_configuration, agents, service_url, knowledge_mode)
            t.problem_definition.default_context["parameters"]["weights"][0] = float(i+1)/float(n_tasks)
            t.problem_definition.default_context["parameters"]["weights"][1] = 1 - t.problem_definition.default_context["parameters"]["weights"][0]
            t.problem_definition.tags.append("collective_learning_test")
            self.tasks.append(t)


def test_collective_learning():
    config = CMAESConfiguration()
    c = TestCreationPipeline()
    c.create_tasks_from_template(rastrigin(), config, 10, "http://localhost:8000", ["localhost"], "local")
    c.create_tasks_from_template(rastrigin(), config, 10, "http://collective-panda-002.local:8000", ["collective-panda-002.local"], "local")
    c.create_tasks_from_template(rastrigin(), config, 10, "http://collective-panda-007.local:8000",
                                 ["collective-panda-007.local"], "local")

    t = TaskScheduler()
    for task in c.tasks:
        t.add_task(task)

    t.solve_tasks()
