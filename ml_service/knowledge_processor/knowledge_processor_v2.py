import logging
import numpy as np
import copy
from knowledge_processor.knowledge_processor_base import KnowledgeProcessorBase


logger = logging.getLogger("ml_service")


class KnowledgeProcessor(KnowledgeProcessorBase):
    def __init__(self, vector_mapping, task_identity, scope, mean_optimum_weights=None, confidence=None):
        super().__init__(vector_mapping, task_identity, scope,  mean_optimum_weights, confidence)

    def _process_knowledge(self, successful_trials: list) -> dict or None:
        '''process raw data from trials to knowledge; working from and on the database'''
        found_depricated_data = False
        clusters = self.find_cluster(successful_trials)
        # use best cluster:
        if len(clusters) == 0:
            logger.error("KnowledgeProcessor.process_knowledge: No clusters found in data. Cant process knowledge.")
            return None

        successful_trials = clusters[0]

        # combine ml data -> knowledge (centroid):
        weights = np.log(len(successful_trials) + 0.5) - np.log(np.arange(1, len(successful_trials) + 1))
        weights /= sum(weights)  # weights like in CMA 'superlinear'
        data = []
        costs = []
        for trial in successful_trials:
            trial_params_dict = trial["theta"]
            trial_params = self.dict_to_list(trial_params_dict)
            data.append(trial_params)
            if "q_metric" in trial:
                costs.append(trial["q_metric"]["final_cost"])
            else:
                costs.append(trial["cost"])
        centroid = np.dot(weights, data)
        expected_cost = float(np.dot(weights, costs))

        logger.debug("knowledge_processor: knowledge successful processed")
        return self.wrap_information(centroid, expected_cost)

    def find_cluster(self, data: list):
        def distance_to(a, b):
            '''distance between 2 multidimensional points'''
            return np.sqrt(sum((np.array(a) - np.array(b)) ** 2))
        logger.debug("knowledge_processor.find_cluster()")
        data = copy.deepcopy(data)
        logger.debug("ClusterProcessor: start working")
        clusters = []

        found_depricated_data = False
        if "q_metric" not in data[0]:
            found_depricated_data = True

        while data:
            # sort for cost
            if not found_depricated_data:
                c_list = sorted(data, key=lambda t: (t["q_metric"]["final_cost"]))  # lowest cost first
            else:
                c_list = sorted(data, key=lambda t: (t["cost"]))  # lowest cost first
            # sorted for distance to best trial:
            d_list = sorted(data, key=lambda t: distance_to(self.dict_to_list(t["theta"]),
                                                            self.dict_to_list(c_list[0]["theta"])))
            cluster = [data.pop(data.index(d_list[0]))]

            if not found_depricated_data:
                for d_trial in d_list[1:]:
                    mean_gradient = 0
                    if len(cluster) >= 2:
                        for trial in cluster[1:]:
                            if distance_to( self.dict_to_list(trial["theta"]), self.dict_to_list(cluster[0]["theta"])) != 0:
                                mean_gradient += (trial["q_metric"]["final_cost"] - cluster[0]["q_metric"]["final_cost"]) / distance_to(
                                    self.dict_to_list(trial["theta"]), self.dict_to_list(cluster[0]["theta"]))
                        mean_gradient = mean_gradient / len(cluster[1:])

                    dist = distance_to(self.dict_to_list(d_trial["theta"]), self.dict_to_list(cluster[0]["theta"]))

                    if d_trial["q_metric"]["final_cost"] > cluster[-1]["q_metric"]["final_cost"]:
                        cluster.append(data.pop(data.index(d_trial)))
                    elif d_trial["q_metric"]["final_cost"] > 0.8 * dist * mean_gradient + cluster[0]["q_metric"]["final_cost"]:
                        cluster.append(data.pop(data.index(d_trial)))
                    else:
                        break
            else:
                for d_trial in d_list[1:]:
                    mean_gradient = 0
                    if len(cluster) >= 2:
                        for trial in cluster[1:]:
                            if distance_to( self.dict_to_list(trial["theta"]), self.dict_to_list(cluster[0]["theta"])) != 0:
                                mean_gradient += (trial["cost"] - cluster[0]["cost"]) / distance_to(
                                    self.dict_to_list(trial["theta"]), self.dict_to_list(cluster[0]["theta"]))
                        mean_gradient = mean_gradient / len(cluster[1:])

                    dist = distance_to(self.dict_to_list(d_trial["theta"]), self.dict_to_list(cluster[0]["theta"]))

                    if d_trial["cost"] > cluster[-1]["cost"]:
                        cluster.append(data.pop(data.index(d_trial)))
                    elif d_trial["cost"] > 0.8 * dist * mean_gradient + cluster[0]["cost"]:
                        cluster.append(data.pop(data.index(d_trial)))
                    else:
                        break

            clusters.append(cluster)

        return clusters
