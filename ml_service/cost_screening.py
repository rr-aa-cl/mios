import numpy as np
from threading import Thread
import uuid

from mongodb_client.mongodb_client import MongoDBClient
from task_scheduler.task_scheduler import Task
from engine.engine import Engine
from engine.engine import Trial
from definitions.insertion_definitions import insert_key
from definitions.insertion_definitions import insert_cylinder
from problem_definition.problem_definition import CostFunction
from experiments.collective_learning_test import rastrigin_a
#from experiments.collective_learning_test import CollectiveLearningBase
from experiments.collective_learning import CollectiveLearningBase
from utils.udp_client import call_method
import logging

logger = logging.getLogger("ml_service")

def update_default_context(x, problem_definition) -> dict:
        logger.debug("BaseService.update_default_context(" + str(x) + ")")
        theta = dict()
        updated_context = problem_definition.default_context
        for i in range(len(problem_definition.domain.vector_mapping)):
            theta[problem_definition.domain.vector_mapping[i]] = x[i]

        logger.debug("BaseService.update_default_context.theta: " + str(theta))

        for p in theta.keys():
            for mapping in problem_definition.domain.context_mapping[p]:
                mapping_categories = mapping.split(".")
                set_nested_parameter(updated_context, mapping_categories,
                                          x[problem_definition.domain.vector_mapping.index(p)])

        return updated_context

def set_nested_parameter(dic, keys, value):
        # logger.debug("BaseService.set_nested_parameter(dic: " + str(dic) + ", " + "keys: " + str(keys) + ")")
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        tmp = keys[-1].split("-")
        if len(tmp) == 1:
            dic[keys[-1]] = value
        elif len(tmp) == 2:
            p_name = tmp[0]
            p_dim = int(tmp[1])
            if p_name not in dic:
                dic[p_name] = []
            if len(dic[p_name]) < p_dim:
                dic[p_name].extend([0] * (p_dim - len(dic[p_name])))
            dic[p_name][p_dim-1] = value
        
def get_theta(x, problem_definition) -> dict:
        logger.debug("BaseService.get_theta(" + str(x) + ")")
        theta = dict()
        for i in range(len(problem_definition.domain.vector_mapping)):
            theta[problem_definition.domain.vector_mapping[i]] = x[i]

        return theta

# config = CMAESConfiguration()
# config.n_gen = 10
# config.n_ind = 13
# config.exploration_mode = False
def optimum_screening(optimum_tags, screening_tags, agent = "collective-panda-001.local", n_samples_pg = 200, max_generations=20, sample_range = [0, 0.1]):
    agent_client = MongoDBClient(agent)
    knowledge = agent_client.read("local_knowledge", "insert_object", {"meta.tags": optimum_tags})[0]
    optimum = knowledge["parameters"]
    optimum_weights = knowledge["meta"]["optimum_weights"]  #[0,1,0,0,0]  # [0,0.5,0.3,0.2,0]
    if len(optimum_weights) != len(CostFunction().optimum_weights):
        logging.error("invalid optimums_weights length")

    problem_definition = insert_cylinder(40, 0.8)
    #problem_definition = rastrigin_a(1)
    problem_definition.cost_function.optimum_weights = optimum_weights
    for t in optimum_tags:
        screening_tags.append(t)
    for t in screening_tags:
        problem_definition.tags.append(t)

    
    call_method(agent, 12002, "set_grasped_object", {"object": "cylinder_40"})

    engine = Engine(set([agent]))
    database_results_id = engine.initialize(problem_definition, True)

    engine_thread = Thread(target=engine.main_loop)
    engine_thread.start()
    import time
    time.sleep(0.1)

    optimum_params = []
    for param in problem_definition.domain.vector_mapping:
        if param in optimum:    
            optimum_params.append(optimum[param])
        else:
            logger.error("param name not in initial optimum!")
    optimum_norm = problem_definition.domain.normalize(optimum_params)
    print("optimum = ", optimum)
    print(database_results_id)


    sample_range = [0, 0.01]   # [starting distance (from optimum), width]
    increase_sample_range = True
    verify = False
    keep_running = True
    cnt_generation = 0
    current_estimated_optimum_width = 0
    while keep_running == True:
        cnt_generation += 1
        print("\n Generation ",cnt_generation)
        uuids = []
        success_count = 0
        for n in range(n_samples_pg):
            # random creation of params (sample_range!)
            if verify:
                # normal distribution: 
                rand_params_normalized = np.random.normal(0, sample_range[1] * 2, len(problem_definition.domain.vector_mapping))
                for i in range(len(rand_params_normalized)):
                    if rand_params_normalized[i] < 0:
                        rand_params_normalized[i] = rand_params_normalized[i] + optimum_norm[i] + sample_range[0] + sample_range[1] 
                    else:
                        rand_params_normalized[i] = rand_params_normalized[i] + optimum_norm[i] - sample_range[0] - sample_range[1] 
            else:
                # uniform distribution:
                rand_params_normalized = np.random.rand(len(problem_definition.domain.vector_mapping))
                for i in range(len(rand_params_normalized)):
                    if rand_params_normalized[i] < 0.5:
                        rand_params_normalized[i] = rand_params_normalized[i] * 2 * sample_range[1] - (sample_range[0] + sample_range[1]) + optimum_norm[i] 
                    else:
                        rand_params_normalized[i] = (rand_params_normalized[i] - 0.5) * 2 * sample_range[1] + sample_range[0] + optimum_norm[i]


            rand_params = problem_definition.domain.denormalize(rand_params_normalized)
            # check for limits:
            for i in range(len(problem_definition.domain.vector_mapping)):
                #lower limit
                if rand_params[i] < problem_definition.domain.limits[problem_definition.domain.vector_mapping[i]][0]:
                    rand_params[i] = problem_definition.domain.limits[problem_definition.domain.vector_mapping[i]][0]
                #upper limit
                if rand_params[i] > problem_definition.domain.limits[problem_definition.domain.vector_mapping[i]][1]:
                    rand_params[i] = problem_definition.domain.limits[problem_definition.domain.vector_mapping[i]][1]
                

            uuids.append(engine.push_trial(Trial(update_default_context(rand_params, problem_definition), problem_definition.reset_instructions,
                                                    get_theta(rand_params, problem_definition))))
        
        for uuid in uuids:
            result = engine.wait_for_trial(uuid, 50).task_result
            # print("final_cost = ", result.final_cost)
            if result.success:
                success_count = success_count + 1
            #if result.final_cost < 0.07:  # just because benchmark is always successful
            #    success_count = success_count + 1
        print("found ",success_count," of ", n_samples_pg, " successful ",  " in sample_range: ", sample_range)
        print("this was verify step: ", verify)
        # if border of optimum is found -> decrease sample_range
        if success_count / n_samples_pg <= 0.95:
            increase_sample_range = False
            alter_sample_range = True
            verify = False
            print("less than 95 percent of samples are within optimum")
        else:
            increase_sample_range = True
            if verify:  # if this step was a verify step
                alter_sample_range = True
                verify = False
                current_estimated_optimum_width = sample_range[0] + sample_range[1]
            else:
                alter_sample_range = False
                verify = True
                

                
            print("all within optimum :)")

        # calculate probability range for next generation
        if alter_sample_range:
            if increase_sample_range:
                sample_range[0] = sample_range[0] + sample_range[1]  # * 0.5
                sample_range[1] = sample_range[1] * 2
            else:
                sample_range[1] = sample_range[1] * 0.5

        if cnt_generation > max_generations:
            keep_running = False
        if cnt_generation == max_generations:  # final validation
            sample_range[0] = 0
            sample_range[1] = current_estimated_optimum_width
            verify = False
            n_samples_pg *= 10
        
        print("current optimum width: ", current_estimated_optimum_width)

    optimum_width_denorm = [current_estimated_optimum_width for i in problem_definition.domain.vector_mapping]
    lower_limits = np.array([problem_definition.domain.limits[key][0] for key in problem_definition.domain.vector_mapping])
    optimum_width_denorm = list(np.array(problem_definition.domain.denormalize(optimum_width_denorm)) + lower_limits)
    data = {"optimum_width_norm": current_estimated_optimum_width, 
            "n_generations": cnt_generation,
            "inspected_optimum": optimum}
    local_client = MongoDBClient()
    local_client.update("ml_results", problem_definition.task_type, {"_id": database_results_id}, {"final_result": data})
    engine.keep_running = False
    time.sleep(3)
    print("Finished :)")

def cost_variance(n_trials = 20, n_repeat = 100, agents = ['collective-panda-001.local'], tags = ["cost_varaince_screening"]):
    e = CollectiveLearningBase()
    e.n_tasks = 1
    e.start(tags=tags, knowledge_mode="none", knowledge_type="none", global_database="localhost", use_cost_grid=None, optima_percentage=1.15, blocking=True)
    problem_definition = e.creation_pipeline.tasks[0].problem_definition
    print(problem_definition)

    client = MongoDBClient(agents[0])
    optimum = client.read("local_knowledge", "insert_object", {"meta.tags":tags})[0]
    optimum = optimum["parameters"]
    print(optimum)

    trials = client.read("ml_results", "insert_object", {"meta.tags":tags})[0]

    engine = Engine(set(agents))
    problem_definition.tags.append("cost_variance_analysis")
    problem_definition.uuid = str(uuid.uuid4())
    database_results_id = engine.initialize(problem_definition, True)

    engine_thread = Thread(target=engine.main_loop)
    engine_thread.start()

    trials.pop("meta", None)
    trials.pop("final_results", None)
    trials.pop("_id", None)
    trials_list = []
    for key in trials.keys():
        trials_list.append(trials[key])
    indexes = np.random.choice(len(trials_list), n_trials, replace=False)

    ids = []
    for i in indexes:
        trial = trials_list[i]
        trial_params = []
        for k in problem_definition.domain.vector_mapping:
            trial_params.append(trial["theta"][k])
        for j in range(n_repeat):
            ids.append(engine.push_trial(Trial(update_default_context(trial_params, problem_definition), problem_definition.reset_instructions,
                                                get_theta(trial_params, problem_definition))))
        for id in ids:
            result = engine.wait_for_trial(id, 50).task_result
    
    client = MongoDBClient()
    results = client.read("ml_results", "insert_object",{"_id": database_results_id})[0]#
    results.pop("meta", None)
    final_results = results.pop("final_result", None)
    mongo_id = results.pop("_id", None)
    if len(results) != n_trials*n_repeat:
        print("Something went wrong!")
        #return -1

    trials_set = set()
    for key in results.keys():
        trials_set.add(tuple(results[key]["theta"].items()))

    n = 0
    for theta in trials_set:
        n += 1
        if final_results is not None:
            final_results["n"+str(n)] = {}
        else:
            final_results = {}
        all_costs = []
        all_tdelta = []
        for key in results.keys():
            if tuple(results[key]["theta"].items()) == theta:
                all_costs.append(results[key]["cost"])
                all_tdelta.append(results[key]["t_delta"])
        cost_mean = float(np.mean(all_costs))
        cost_std = float(np.std(all_costs))
        tdelta_mean = float(np.mean(all_tdelta))
        tdelta_std = float(np.std(all_tdelta))
        final_results["n"+str(n)] = {"cost_mean": cost_mean,
                                     "cost_std": cost_std,
                                     "t_delta_mean": tdelta_mean,
                                     "t_delta_std": tdelta_std,
                                     "theta": dict(theta)}
    client.update("ml_results", "insert_object", {"_id": mongo_id},{"final_results": final_results})
        
    return optimum

if __name__ == "__main__":
    optimum_screening(["cost_varaince_screening"], ["optimum_screening"], agent="collective-panda-001.local", n_samples_pg=5, max_generations=5,sample_range=[0,0.1])
    #cost_variance()
    print("finished :)")

    

