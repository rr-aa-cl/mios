from threading import currentThread
from plotting.result import Result
import numpy as np
import scipy.stats
from typing import Tuple


class DataError(Exception):
    pass


class DataProcessor:
    def __init__(self):
        pass

    def find_maximum_length(self, lists: list):
        length = 0
        for l in lists:
            if len(l) > length:
                length = len(l)
        return length

    def get_collection_of_successes(self, results: list) -> list:
        successes = []
        for r in results:
            successes.append(r.get_successes_per_trial())

        n_trials = self.find_maximum_length(successes)

        for s in successes:
            if len(s) < n_trials:
                s.extend([s[-1]] * (n_trials - len(s)))
        return successes

    def get_collection_of_successes_over_time(self, results: list, min_length: int = False) -> list:
        successes = []
        times = []
        max_span = 0
        for r in results:
            success, time = r.get_successes_per_time()
            if time[-1] - time[0] > max_span:
                max_span = time[-1] - time[0]
            times.append(time)
            successes.append(success)

        max_span = int(np.ceil(max_span))
        success_over_time = []
        for i in range(len(successes)):
            success_over_time.append([0] * max_span)
            current_cost = successes[i][0]
            cnt_cost = 0
            for j in range(max_span):
                if j > times[i][cnt_cost]:
                    current_cost = successes[i][cnt_cost]
                    if cnt_cost < len(times[i]) - 1:
                        cnt_cost += 1
                success_over_time[i][j] = current_cost
            if min_length is not False and len(success_over_time[i]) < min_length:
                success_over_time[i].extend([success_over_time[i][-1]] * (min_length - len(success_over_time[i])))
        return success_over_time

    def get_collection_of_costs(self, results: list, decreasing: bool = False, episode_length: int = 1, agent:str=None, specification: str = "all", cost_type:str=None, equal_length:bool = True) -> list:
        costs = []
        for r in results:
            if decreasing is True:
                costs.append(self.get_monotonically_decreasing_cost(r.get_cost_per_trial(episode_length, cost_type, agent, specification)))
            else:
                costs.append(r.get_cost_per_trial(episode_length, cost_type, agent, specification))

        n_trials = self.find_maximum_length(costs)

        if equal_length:
            for c in costs:
                if len(c) < n_trials:
                    c.extend([c[-1]] * (n_trials - len(c)))
        return costs

    def get_collection_of_times(self, results: list, agent:str=None, specification: str = "all", cost_type:str=None, equal_length:bool = True) -> list:
        times = []
        for r in results:
            times.append(r.get_cost_per_timestemp(cost_type, agent))

        n_trials = self.find_maximum_length(times)

        if equal_length:
            for c in times:
                if len(c) < n_trials:
                    c.extend([c[-1]] * (n_trials - len(c)))
        return costs

    def get_collection_of_costs_over_time(self, results: list, min_length: int = False, decreasing: bool = False, agent=None) -> list:
        costs = []
        times = []
        max_span = 0
        for r in results:
            cost, time = r.get_cost_per_time(agent)
            if time[-1] - time[0] > max_span:
                max_span = time[-1] - time[0]
            times.append(time)
            if decreasing is True:
                costs.append(self.get_monotonically_decreasing_cost(cost))
            else:
                costs.append(cost)

        max_span = int(np.ceil(max_span))
        cost_over_time = []
        for i in range(len(costs)):
            cost_over_time.append([0] * max_span)
            current_cost = costs[i][0]
            cnt_cost = 0
            for j in range(max_span):
                if j > times[i][cnt_cost]:
                    current_cost = costs[i][cnt_cost]
                    if cnt_cost < len(times[i]) - 1:
                        cnt_cost += 1
                cost_over_time[i][j] = current_cost
            if min_length is not False and len(cost_over_time[i]) < min_length:
                cost_over_time[i].extend([cost_over_time[i][-1]] * (min_length - len(cost_over_time[i])))
        return cost_over_time

    def get_optima_by_task_identity(self, results: list, percentage: float) -> np.ndarray:
        arr = np.zeros((len(results), 7))
        for i in range(len(results)):
            if len(results[i].trials) < 1:
                continue
            arr[i, 0] = results[i].meta_data["cost_function"]["geometry_factor"]
            arr[i, 1:-1] = results[i].meta_data["cost_function"]["optimum_weights"]
            cost_grid_max = np.asarray(results[i].meta_data["cost_function"]["max_cost"])
            max_cost = cost_grid_max[0] * arr[i, 1] + cost_grid_max[1] * arr[i, 2] + cost_grid_max[2] * arr[i, 3] + \
                       cost_grid_max[3] * arr[i, 4] + cost_grid_max[4] * arr[i, 5]
            cost = self.get_monotonically_decreasing_cost(results[i].get_cost_per_trial())
            max_cost = 1
            arr[i, -1] = percentage * cost[-1]
        return arr
    
    def get_average_time(self, results: list, episode_length: int = 1, agent=None, specification:str="all", cutoff:float = False):
        cost, times = self.get_cost_over_timestemp(results, cutoff)  # timestemp t_1  - starting_time
        total_times = []
        for single_run_times in times:
            total_times.append(single_run_times[-1])
        interval = []
        interval = scipy.stats.t.interval(alpha=0.95, df=len(total_times)-1, loc=np.mean(total_times), scale=scipy.stats.sem(total_times))
        return np.mean(total_times), interval

    def get_average_cost(self, results: list, decreasing: bool = False, episode_length: int = 1, agent=None) -> Tuple[np.ndarray, np.ndarray]:
        cost = np.asarray(self.get_collection_of_costs(results, decreasing, episode_length, agent))
        confidence = 0.95
        interval = []
        for i in range(cost.shape[1]):
            se = scipy.stats.sem(cost[:, i])
            h = se * scipy.stats.t.ppf((1 + confidence) / 2., cost.shape[0] - 1)
            interval.append(h)
        return np.average(cost, 0), np.asarray(interval)
        #return np.average(np.asarray(self.get_collection_of_costs(results, decreasing, episode_length, agent)), 0)

    def get_average_success(self, results: list) -> Tuple[np.ndarray, np.ndarray]:
        success = np.asarray(self.get_collection_of_successes(results))
        confidence = 0.95
        interval = []
        for i in range(success.shape[1]):
            se = scipy.stats.sem(success[:, i])
            h = se * scipy.stats.t.ppf((1 + confidence) / 2., success.shape[0] - 1)
            interval.append(h)
        return np.average(success, 0), np.asarray(interval)

    def get_average_cost_over_time(self, results: list, min_length: int = False, decreasing: bool = False, agent=None, specification: str = "all") -> Tuple[np.ndarray, np.ndarray]:
        cost = np.asarray(self.get_collection_of_costs_over_time(results, min_length, decreasing, agent))
        print(np.std(cost))
        confidence = 0.95
        interval = []
        for i in range(cost.shape[1]):
            se = scipy.stats.sem(cost[:, i])
            h = se * scipy.stats.t.ppf((1 + confidence) / 2., cost.shape[0] - 1)
            interval.append(h)
        return np.average(cost, 0), np.asarray(interval)
    
    def get_average_cost_over_agerage_time(self, results: list, min_length: int = False):
        pass
    
    def get_average_cost_over_timestemp(self, results: list, min_length: int = False, cutoff = False) -> Tuple[np.ndarray, np.ndarray]:
        cost = []
        time = []
        starting_time = []
        mean_cutoff_index = []
        for r in results:
            if min_length:
                print("min_length: ",min_length, " actual length:",len(r.costs))
                cost.append(self.get_monotonically_decreasing_cost(r.costs[:min_length]))
                if len(cost[-1]) < min_length:
                    cost[-1].extend([cost[-1][-1]] * (min_length - len(cost[-1])))
                time.append(r.times[:min_length])
                if len(time[-1]) < min_length:
                    time[-1].extend([time[-1][-1]] * (min_length - len(time[-1])))
            else:
                cost.append(self.get_monotonically_decreasing_cost(r.costs))
                time.append(r.times)
            starting_time.append(r.starting_time)
            mean_cutoff_index.append(next((x for x in range(len(cost[-1])) if cost[-1][x]<cutoff), len(cost[-1])-1))
        cost =  np.asarray(cost)
        time =  np.asarray(time)    
        confidence = 0.95
        interval_cost = []
        interval_time = []
        for i in range(cost.shape[1]):
            se = scipy.stats.sem(cost[:, i])
            h = se * scipy.stats.t.ppf((1 + confidence) / 2., cost.shape[0] - 1)
            interval_cost.append(h)

            se = scipy.stats.sem(time[:, i])
            h = se * scipy.stats.t.ppf((1 + confidence) / 2., time.shape[0] - 1)
            interval_time.append(h)
        return np.average(cost, 0), np.asarray(interval_cost), np.average(time, 0), np.asarray(interval_time), np.average(starting_time, 0), int(np.ceil(np.mean(mean_cutoff_index)))+1
    
    def get_cost_over_timestemp(self, results:list, cutoff:float = False):
        costs = []
        times = []
        for r in results:
            costs.append(self.get_monotonically_decreasing_cost(r.costs))
            times.append(r.times)
            if cutoff:
                for i in range(len(costs[-1])):
                    if costs[-1][i] <= cutoff:
                        costs[-1] = costs[-1][:i+1]
                        times[-1] = times[-1][:i+1]
                        break
        return costs, times

    def get_average_cost_over_trials(self, results: list, decreasing: bool = False, episode_length: int = 1, agent=None, specification: str = "all") -> Tuple[np.ndarray, np.ndarray]:
        cost = np.asarray(self.get_collection_of_costs(results, decreasing, episode_length, agent, specification=specification))
        confidence = 0.95
        interval = []
        for i in range(cost.shape[1]):
            se = scipy.stats.sem(cost[:, i])
            h = se * scipy.stats.t.ppf((1 + confidence) / 2., cost.shape[0] - 1)
            interval.append(h)
        return np.average(cost, 0), np.asarray(interval)
    
    def get_average_n_trials(self, results: list, episode_length: int = 1, agent=None, specification:str="all", cutoff:float = False):
        cost_collection = np.asarray(self.get_collection_of_costs(results, False, episode_length, agent, specification=specification, equal_length=False))
        confidence = 0.95
        interval = []
        data = []
        for costs in cost_collection:
            if cutoff:
                index = len(costs)
                for i in range(len(costs)):
                    if costs[i] < cutoff:
                        index = i
                        break
                costs = costs[:index+1]
            data.append(len(costs))
        print(data, "\n number of experiments: ", len(data))
        interval = scipy.stats.t.interval(alpha=0.95, df=len(data)-1, loc=np.mean(data), scale=scipy.stats.sem(data))
        return np.mean(data), interval
    
    def get_average_cost_over_batch(self, results: list, decreasing: bool = False, episode_length: int = 1, agent=None) -> Tuple[np.ndarray, np.ndarray]:
        cost = np.asarray(self.get_collection_of_costs(results, decreasing, episode_length, agent))
        confidence = 0.95
        interval = []
        for i in range(cost.shape[1]):
            se = scipy.stats.sem(cost[:, i])
            h = se * scipy.stats.t.ppf((1 + confidence) / 2., cost.shape[0] - 1)
            interval.append(h)
        return np.average(cost, 0), np.asarray(interval)

    def get_average_success_over_time(self, results: list, min_length: int = False) -> Tuple[np.ndarray, np.ndarray]:
        success = np.asarray(self.get_collection_of_successes_over_time(results, min_length))
        confidence = 0.95
        interval = []
        for i in range(success.shape[1]):
            se = scipy.stats.sem(success[:, i])
            h = se * scipy.stats.t.ppf((1 + confidence) / 2., success.shape[0] - 1)
            interval.append(h)
        return np.average(success, 0), np.asarray(interval)

    def get_monotonically_decreasing_cost(self, cost: np.ndarray) -> np.ndarray:
        cost_monotone = cost
        if len(cost_monotone) == 0:
            raise DataError
        c_0 = cost_monotone[0]
        for i in range(1, len(cost_monotone)):
            if cost[i] > c_0:
                cost_monotone[i] = c_0
            if cost_monotone[i] < c_0:
                c_0 = cost_monotone[i]
        return cost_monotone

    def get_total_times(self, results: list) -> np.ndarray:
        times = []
        for r in results:
            times.append(r.get_total_time())
        return np.asarray(times)

    def get_parameter_over_cost(self, result: Result, parameter: str) -> Tuple[list, list]:
        cost = result.get_cost_per_trial()
        parameters = result.get_theta_per_trial()
        p = []
        for i in range(len(parameters)):
            p.append(parameters[i][parameter])

        cost_sorted = [x for _, x in sorted(zip(p, cost))]
        return cost_sorted, sorted(p)

    def get_agent_results(self, results: list) -> dict:
        agents = []
        ordered_results = {}
        for r in results:
            tags = set(r.meta_data["tags"])
            if tags not in agents:
                agents.append(tags)
                ordered_results[str(tags)] = []
                ordered_results[str(tags)].append(r)
            else:
                ordered_results[str(tags)].append(r)
        return ordered_results

    def get_cumulative_time(self, results: list) -> np.ndarray:
        times_cum = []
        for r in results:
            if len(times_cum) == 0:
                times_cum.append(r.get_total_time())
            else:
                times_cum.append(times_cum[-1] + r.get_total_time())
        return np.asarray(times_cum)

    def get_total_trials(self, results: list) -> np.ndarray:
        trials_per_task = []
        for r in results:
            trials_per_task.append(r.get_total_trials())
        return np.asarray(trials_per_task)

    def sort_over_time(self, results: list) -> list:  # sort over end-time
        return sorted(results, key=lambda r: (r.starting_time + r.total_time))

    def get_average_theta(self):
        pass

    def get_std_cost(self, results: list) -> np.ndarray:
        return np.std(np.asarray(self.get_collection_of_costs(results)), 0)

    def get_std_theta(self):
        pass

    def dict_to_list(self, d: dict) -> list:
        '''returns a list with dict contents'''
        l = []
        for key in d.keys():
            l.append(d[key])
        return l

    def mean_confidence_interval(data, confidence=0.95):
        a = 1.0 * np.array(data)
        n = len(a)
        m, se = np.mean(a), scipy.stats.sem(a)
        h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
        return m, h
    
    def get_cost_difference_curve(self, results_1, results_2):
        cost1 = self.get_average_cost(results_1, True)
        cost2 = self.get_average_cost(results_2, True)
        cost_space = np.linspace(0, np.max([np.max(cost1), np.max(cost2)]), 1000)
        curve1 = []
        curve2 = []
        for inc in cost_space:
            curve1.append(len(cost1[cost1<inc]))
        for inc in cost_space:
            curve2.append(len(cost2[cost2<inc]))

        difference = []
        for i in range(len(cost_space)):
            difference.append(abs(curve1[i] - curve2[i]))
        print(difference)

    def get_cost_of_successes(self, results: list):
        successes = []
        for result in results:
            result_successes = []
            for trial in result.trials:
                if trial["q_metric"]["success"]:
                    result_successes.append(trial["q_metric"]["final_cost"])
            successes.append(result_successes)
        return successes
