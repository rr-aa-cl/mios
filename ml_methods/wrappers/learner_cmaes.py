import numpy as np
import random
import deap

from deap import algorithms
from copy import deepcopy
from deap import base
from deap import cma
from deap import creator
from deap import tools

from ml_methods.wrappers.learner_base import LearnerBase


class LearnerCMAES(LearnerBase):
    def __init__(self):
        super(LearnerCMAES, self).__init__()

        self.constraints_multiplier = []
        self.failure_cost = None
        self.constraints_base_cost = None
        self.n_gen = None
        self.n_ind = None
        self.adapt_to_agents = None
        self.n_ext = None
        self.n_rep = None
        self.sigma_init = None
        self.target_cost = None
        self.centroid_init = None
        self.strategy = None
        self.champion = None
        self.champion_old = None
        self.cm_opt = None
        self.cm_opt_old = None
        self.population = None

        self.cnt_ind = 0
        self.cnt_gen = 0

        self.bounds = []
        self.bounds_feasibility = []

    def _init_learner(self):
        self.cnt_ind = 0
        deap.creator.create("FitnessMin", deap.base.Fitness, weights=(-1.0,))
        deap.creator.create("Individual", list, fitness=deap.creator.FitnessMin)
        self.toolbox = deap.base.Toolbox()

    def _learn_task(self):

        # calculate center wrt bounds
        self.mat_bounds = []
        for p in self.domain:
            self.mat_bounds.append(p["bounds"])

        self.mat_bounds = np.array(self.mat_bounds)

        if self.base_params is not None:
            self.centroid_init = dict()
            for i in range(len(self.domain)):
                # x_init[i]=(self.domain[i]['bounds'][1]-self.domain[i]['bounds'][0])/2
                for key, val in self.base_params.items():
                    if self.domain[i]['name'] == key:
                        print('%s has value: %s' % (self.domain[i]['name'], val))
                        if val < self.mat_bounds[i,0]:
                            val = self.mat_bounds[i,0]
                            print('Value ' + self.domain[i]['name'] + ' is out of bounds, shifting to lower bound.')
                        if val > self.mat_bounds[i,1]:
                            val = self.mat_bounds[i,1]
                            print('Value ' + self.domain[i]['name'] + ' is out of bounds, shifting to upper bound.')
                        self.centroid_init[key] = self._normalize2(val, self.mat_bounds[i, 0], self.mat_bounds[i, 1])
                        print('%s has normal value: %s' % (self.domain[i]['name'], self.centroid_init[key]))

        if self.centroid_init is not None:
            x_init = [0.0] * len(self.domain)
            for i in range(len(self.domain)):
                # x_init[i]=(self.domain[i]['bounds'][1]-self.domain[i]['bounds'][0])/2
                for key, val in self.centroid_init.items():
                    if self.domain[i]['name'] == key:
                        print('%s has value: %s' % (self.domain[i]['name'], val))
                        x_init[i] = val

            centroid = x_init

        else:
            print('No prior knowledge available and no initial centroid given, reverting to standard.')
            centroid = 0.0 * np.ones(len(self.mat_bounds))

        self.cnt_gen = 0

        self.toolbox.register("evaluate", self._run_trial)
        self.toolbox.register("map", self._run_trial_par)

        if self.adapt_to_agents is True:
            self.n_ind = len(self.hosts)
        self.strategy = deap.cma.Strategy(centroid=centroid, sigma=self.sigma_init,
                                          mu=self.n_ind - int(self.n_ind / 1.5), lambda_=self.n_ind,
                                          weights="superlinear")
        self.toolbox.register("generate", self.strategy.generate, deap.creator.Individual)
        self.toolbox.register("update", self.strategy.update)

        hof = deap.tools.HallOfFame(self.n_ind)

        stats = deap.tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)

        self.eaGenerateUpdate(self.toolbox, ngen=self.n_gen, stats=stats, halloffame=hof)

        self.champion = hof[0]
        self.cm_opt = self.strategy.C

        print('Champion: ', self._unnormalize(self.champion))
        print('CM: ', self.cm_opt)

        self.problem_data = {
            "parameters": dict(),
            "cost": self.champion.fitness.values[0],
            "success": True
        }

        params = self._unnormalize(self.champion)

        for i in range(len(self.domain)):
            self.problem_data["parameters"][self.domain[i]["name"]] = params[i]

        if self.target_cost is not None:
            if self.champion.fitness.values[0] > self.target_cost:
                print('Target cost not reached')
                return False
            else:
                print('Target cost reached')
                return True
        else:
            return True

    def _run_trial_par(self, f, input):
        """ create array of rpc params for input """
        try:
            cnt_ind = 0
            print("Evaluating generation " + str(self.cnt_gen))
            self.cnt_gen += 1
            id_ = 0
            results = [False] * len(input)
            costs = len(input) * [(-1,)]
            selector = []
            input_tmp = deepcopy(input)

            print("########################################")
            print("LEN: " + str(len(costs)))
            print("########################################")

            if self.preknowledge is not None and self.preknowledge["source"] == "global" \
                    and self.url_lookup["knowledge_base"] is not None:
                n_samples_d = int(np.ceil(self.n_ind / 2))
                n_samples_d = 3
                response_hints = None
                if self.preknowledge["source"] == "global":
                    response_hints = self.rpc_call(self.url_lookup["knowledge_base"], "pull_hints",
                                                   {"identity": self.problem["identity"], "n_samples": n_samples_d,
                                                    "hints_uuid": list(self.hints_uuid)})
                if response_hints is None:
                    print("Knowledge server may not be reachable.")
                elif response_hints["result"] is None:
                    print("No knowledge available.")
                else:
                    samples = response_hints["result"]["data"]
                    n_samples = len(samples)
                    selector = np.linspace(0, len(input) - 1, len(input)).astype(int).tolist()
                    random.shuffle(selector)
                    selector = selector[0:n_samples]

                    for i in range(n_samples):
                        input_tmp[selector[i]] = samples[i]["parameters"]
                        costs[selector[i]] = (samples[i]["cost"],)
                        results[selector[i]] = samples[i]["success"]
                        data_sample = dict()
                        data_sample["success"] = results[selector[i]]
                        data_sample["cost"] = costs[selector[i]][0]
                        self.data.append(data_sample)

                        for j in range(len(self.population[selector[i]])):
                            self.population[selector[i]][j] = input_tmp[selector[i]][j]

            for x in input_tmp:
                for i in range(len(x)):
                    if x[i] < 0:
                        x[i] = 0
                    if x[i] > 1:
                        x[i] = 1
                x_n = x
                x = self._unnormalize(x)
                for i in range(len(x)):
                    if self.domain[i]['name'] == 'gamma_b_t' or self.domain[i]['name'] == 'gamma_b_r':
                        tmp = self._unnormalize2(1 - x_n[i], np.log10(1 / self.mat_bounds[i, 1]),
                                                 np.log10(1 / self.mat_bounds[i, 0]))
                        x[i] = 1 / pow(10, tmp)

                params = deepcopy(self.param_template)
                #            params['skills'] = self.definition['skills']
                # print(params)

                for i in range(len(x)):
                    param_keys = str.split(str(self.domain[i]['name']), ".")
                    param_keys[len(param_keys) - 1] = str.split(str(param_keys[len(param_keys) - 1]), '-')[0]
                    self._set_param(x[i], i, params)

                param_log = deepcopy(params)

                job = dict()
                job["params"] = params
                job["reset_instructions"] = deepcopy(self.definition["reset_instructions"])
                job["param_log"] = param_log
                job["id"] = id_
                job["params_normalized"] = x_n
                job["params_pure"] = x
                job["n_trial"] = self.n_trial
                # job["n_limit_violations"] = n_limit_violations
                id_ += 1

                if cnt_ind not in selector:
                    self.job_queue.put(deepcopy(job))
                    self.n_trial += 1

                cnt_ind += 1

            print("Evaluation batch of size %d..." % len(input_tmp))
            self.job_queue.join()
            print("EVAL")

            params = len(input_tmp) * [len(input_tmp[0]) * [None]]
            if self.strategy is not None:
                print('Sigma: ' + str(self.strategy.sigma))

            while not self.job_completed.empty():
                done_job = self.job_completed.get()

                if "response" in done_job:
                    response = done_job["response"]
                    success = response["success"]
                    cost_suc = response["cost_suc"]
                    cost_err = response["cost_err"]
                    nominal = response["nominal_termination"]
                    # if nominal is False:
                    # print("A task did not terminate nominally, stopping learning process.")
                    if success is False:
                        # cost_final = self.failure_base_cost + np.exp(cost_err * 100) - 1
                        cost_final = cost_err
                    else:
                        cost_final = cost_suc

                    if np.isnan(cost_final) or np.isinf(cost_final) or cost_final < 0 or cost_final is None:
                        cost_final = 1000000000
                    self._write_meta_data(done_job["n_trial"], done_job["param_log"], cost_final, success,
                                          done_job["t_start"], done_job["t_finish"])
                else:
                    cost_final = 1000000000
                    success = False

                costs[done_job["id"]] = (cost_final,)
                results[done_job["id"]] = success
                # params[done_job["id"]]= done_job["params_pure"]
                self.job_completed.task_done()

            print("Done")

            costs_tmp = []
            for c in costs:
                costs_tmp.append(c[0])

            return costs
        except TypeError as e:
            print("Key error: " + str(e))
            return len(input) * [(0,)]

    def _run_trial(self, x):
        print('RUN_TRIAL')
        pass

    def _read_local_options(self, default_options):

        self.n_gen = self.read_option('n_gen', default_options)
        self.sigma_init = self.read_option('sigma_init', default_options)
        self.failure_base_cost = self.read_option('failure_base_cost', default_options)
        self.n_ind = self.read_option('n_ind', default_options)
        self.adapt_to_agents = self.read_option('adapt_to_agents', default_options)
        self.n_ext = 0

        if 'options' not in self.definition:
            print("No learner options for this task, reverting to standard")
            return True

        if 'cmaes' not in self.definition['options']:
            print("No learner options for this task, reverting to standard")
            return True

        options_overwrite = self.definition["options"]["cmaes"]
        if 'target_cost' in options_overwrite:
            self.target_cost = options_overwrite['target_cost']

        if 'n_gen' in options_overwrite:
            self.n_gen = options_overwrite['n_gen']

        if 'n_ind' in options_overwrite:
            self.n_ind = options_overwrite['n_ind']

        if 'adapt_to_agents' in options_overwrite:
            self.adapt_to_agents = options_overwrite['adapt_to_agents']

        if 'n_ext' in options_overwrite:
            self.n_ind = options_overwrite['n_ext']

        if 'sigma_init' in options_overwrite:
            self.sigma_init = options_overwrite['sigma_init']

        if 'failure_base_cost' in options_overwrite:
            self.failure_base_cost = options_overwrite['failure_base_cost']

        if 'centroid_init' in options_overwrite:
            self.centroid_init = options_overwrite['centroid_init']

        return True

    def _normalize(self, x):
        return (x - self.mat_bounds[:, 0]) / (self.mat_bounds[:, 1] - self.mat_bounds[:, 0])

    def _normalize2(self, x, min_, max_):
        return (x - min_) / (max_ - min_)

    def _unnormalize(self, x):
        return x * (self.mat_bounds[:, 1] - self.mat_bounds[:, 0]) + self.mat_bounds[:, 0]

    def _unnormalize2(self, x, min_, max_):
        return x * (max_ - min_) + min_

    def _transform_to_real(self,x):
        x_n = x
        x = self._unnormalize(x)
        for i in range(len(x)):
            if self.domain[i]['name'] == 'gamma_b_t' or self.domain[i]['name'] == 'gamma_b_r':
                tmp = self._unnormalize2(1 - x_n[i], np.log10(1 / self.mat_bounds[i, 1]),
                                         np.log10(1 / self.mat_bounds[i, 0]))
                x[i] = 1 / pow(10, tmp)

        return x

    def eaGenerateUpdate(self, toolbox, ngen, halloffame=None, stats=None,
                         verbose=__debug__):
        """This is algorithm implements the ask-tell model proposed in
        [Colette2010]_, where ask is called `generate` and tell is called `update`.

        :param toolbox: A :class:`~deap.base.Toolbox` that contains the evolution
                        operators.
        :param ngen: The number of generation.
        :param stats: A :class:`~deap.tools.Statistics` object that is updated
                      inplace, optional.
        :param halloffame: A :class:`~deap.tools.HallOfFame` object that will
                           contain the best individuals, optional.
        :param verbose: Whether or not to log the statistics.
        :returns: The final population
        :returns: A class:`~deap.tools.Logbook` with the statistics of the
                  evolution

        The algorithm generates the individuals using the :func:`toolbox.generate`
        function and updates the generation method with the :func:`toolbox.update`
        function. It returns the optimized population and a
        :class:`~deap.tools.Logbook` with the statistics of the evolution. The
        logbook will contain the generation number, the number of evalutions for
        each generation and the statistics if a :class:`~deap.tools.Statistics` is
        given as argument. The pseudocode goes as follow ::

            for g in range(ngen):
                population = toolbox.generate()
                evaluate(population)
                toolbox.update(population)

        .. [Colette2010] Collette, Y., N. Hansen, G. Pujol, D. Salazar Aponte and
           R. Le Riche (2010). On Object-Oriented Programming of Optimizers -
           Examples in Scilab. In P. Breitkopf and R. F. Coelho, eds.:
           Multidisciplinary Design Optimization in Computational Mechanics,
           Wiley, pp. 527-565;

        """
        logbook = tools.Logbook()
        logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])
        self.population = None

        for gen in range(ngen):
            # Generate a new population
            self.population = toolbox.generate()
            # Evaluate the individuals
            #try:
            fitnesses = toolbox.map(toolbox.evaluate, self.population)
            for ind, fit in zip(self.population, fitnesses):
                ind.fitness.values = fit
                self.top_samples.append(fit[0])
            #except TypeError:
            #    print('Encountered exception during learning, aborting.')
            #    break

            if halloffame is not None:
                halloffame.update(self.population)

            # Update the strategy with the evaluated individuals
            toolbox.update(self.population)

            record = stats.compile(self.population) if stats is not None else {}
            logbook.record(gen=gen, nevals=len(self.population), **record)
            if verbose:
                print(logbook.stream)

            if self.flag_stop is True:
                break

        return self.population, logbook
