import time
from xmlrpc.client import ServerProxy, Transport

from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from services.knowledge import Knowledge
from utils.experiment_wizard import start_experiment
from definitions.templates import InsertionFactory
from definitions.cost_functions import TimeMetric
from definitions.service_configs import SVMLearner, CMAESLearner
from utils.ws_client import call_method

# Fixed motion settings: contact search, initial joint travel, and return.
# The contact speed seeds the first candidate; subsequent trials learn it.
FIRST_CONTACT_SPEED = 0.02  # m/s
SUPERVISED_SETUP_JOINT_SPEED = 0.10  # rad/s
SUPERVISED_SETUP_JOINT_ACCELERATION = 0.20  # rad/s^2
SUPERVISED_RETURN_JOINT_SPEED = 0.05  # rad/s
SUPERVISED_RETURN_JOINT_ACCELERATION = 0.10  # rad/s^2
RETURN_CARTESIAN_SPEED = (0.02, 0.10)  # m/s, rad/s
RETURN_CARTESIAN_ACCELERATION = (0.10, 0.20)  # m/s^2, rad/s^2


def supervised_nominal_knowledge(problem_definition):
    """Keep the nominal taught pose and set the first contact-search speed.

    Domain.x_0 uses values in [0, 1], while Knowledge.parameters expects
    physical units. Convert once, then override only the contact speed,
    preserving the factory's zero pose offsets and full learning ranges.
    """
    domain = problem_definition.domain
    initial_values = domain.denormalize(domain.get_default_x0())
    parameters = {
        parameter: float(value)
        for parameter, value in zip(domain.vector_mapping, initial_values)
    }
    if set(parameters) != set(domain.limits):
        raise RuntimeError("Nominal supervised parameters do not match the insertion domain.")
    lower, upper = domain.limits["p1_dx_d"]
    if not lower <= FIRST_CONTACT_SPEED <= upper:
        raise ValueError("FIRST_CONTACT_SPEED must be within the insertion domain's p1_dx_d range.")
    parameters["p1_dx_d"] = FIRST_CONTACT_SPEED
    return Knowledge(mode=None, parameters=parameters, confidence=0.0).to_dict()


def configure_supervised_motion(problem_definition):
    """Configure initial travel and slower extraction/return independently.

    ``MoveToPoseJoint`` defaults to MIOS control mode 3, which emits a joint
    velocity command.  The commissioned effort controller deliberately does
    not accept that command mode; it accepts the joint-torque pipeline's
    bounded effort output instead. Keep mode 1 for every joint move.
    ``TaxExtraction`` uses separate Cartesian limits for withdrawal and
    orientation; changing joint travel speed alone cannot slow that return.
    """
    instruction_groups = (
        (problem_definition.setup_instructions,
         SUPERVISED_SETUP_JOINT_SPEED, SUPERVISED_SETUP_JOINT_ACCELERATION),
        (problem_definition.reset_instructions,
         SUPERVISED_RETURN_JOINT_SPEED, SUPERVISED_RETURN_JOINT_ACCELERATION),
        (problem_definition.rescue_instructions,
         SUPERVISED_RETURN_JOINT_SPEED, SUPERVISED_RETURN_JOINT_ACCELERATION),
        (problem_definition.termination_instructions,
         SUPERVISED_RETURN_JOINT_SPEED, SUPERVISED_RETURN_JOINT_ACCELERATION),
    )
    for instructions, speed, acceleration in instruction_groups:
        for instruction in instructions:
            context = instruction.get("parameters", {})
            parameters = context.get("parameters", {})
            names = parameters.get("skill_names", [])
            types = parameters.get("skill_types", [])
            skills = context.get("skills", {})
            for name, skill_type in zip(names, types):
                if skill_type not in ("MoveToPoseJoint", "TaxExtraction"):
                    continue
                move = skills.get(name)
                if not isinstance(move, dict):
                    raise RuntimeError(
                        f"Missing {skill_type} context for supervised skill {name!r}."
                    )
                if skill_type == "MoveToPoseJoint":
                    move.setdefault("control", {})["control_mode"] = 1  # mJointTorque
                    move.setdefault("skill", {})["speed"] = speed
                    move["skill"]["acc"] = acceleration
                else:
                    for phase_name in ("p0", "p1"):
                        phase = move.get("skill", {}).get(phase_name)
                        if not isinstance(phase, dict):
                            raise RuntimeError(f"Missing {phase_name} in extraction skill {name!r}.")
                        phase["dX_d"] = list(RETURN_CARTESIAN_SPEED)
                        phase["ddX_d"] = list(RETURN_CARTESIAN_ACCELERATION)



def learn_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 10, keep_record: bool = False, knowledge = None, wait: bool = False, service_port:int = 8000):
    start_experiment(robot, [robot], problem_definition, service_config, n_iterations, knowledge=knowledge, tags=tags,
                     keep_record=keep_record, wait=wait,service_port=service_port)


def set_active_grasped_object(robot: str, object_name: str):
    """Align Core's task context with an object that is already clamped."""
    response = call_method(robot, 12000, "set_grasped_object", {"object": object_name})
    result = response.get("result") if isinstance(response, dict) else None
    result = result if isinstance(result, dict) else {}
    if result.get("result") is True:
        return

    # Core updates the logical object before applying robot parameters. The
    # ROS parameter gate can reject that final step; verify the object readback.
    state = call_method(robot, 12000, "get_state", {}, timeout=5,
                        open_timeout=5, close_timeout=0.2)
    state_result = state.get("result") if isinstance(state, dict) else None
    active_object = (
        state_result.get("grasped_object")
        if isinstance(state_result, dict) and state_result.get("result") is True
        else None
    )
    if active_object != object_name:
        raise RuntimeError(
            f"Could not set active grasped object to {object_name!r}: "
            f"{result.get('error', response)}"
        )


def check_taught_insertion_objects(robot: str, insertable: str):
    """Require the three saved teaching contexts before changing robot state."""
    if not isinstance(insertable, str) or not insertable.strip():
        raise ValueError("The insertable must be a non-empty taught object name.")
    missing = []
    for name in (insertable, insertable + "_container_approach", insertable + "_container"):
        response = call_method(robot, 12000, "download_object_context", {"object": name},
                               timeout=5, open_timeout=5, close_timeout=0.2)
        result = response.get("result") if isinstance(response, dict) else None
        context = result.get("context") if isinstance(result, dict) else None
        if (not isinstance(result, dict) or result.get("result") is not True
                or not isinstance(context, dict) or context.get("name") != name):
            missing.append(name)
    if missing:
        raise RuntimeError(
            f"Missing or unreadable taught object contexts on Core {robot}: {', '.join(missing)}. "
            "Use exactly the same object name in mios_examples.py and example_learning.py, "
            "and complete teaching of the grasp, approach, and container poses first."
        )


class _ServiceTransport(Transport):
    def make_connection(self, host):
        connection = super().make_connection(host)
        connection.timeout = 5
        return connection


def check_learning_services(robot, service_port=8000):
    """Check Core and ML reachability before claiming arm command interfaces."""
    response = call_method(robot, 12000, "get_state", {}, timeout=5,
                           open_timeout=5, close_timeout=0.2)
    result = response.get("result") if isinstance(response, dict) else None
    if not isinstance(result, dict) or result.get("result") is not True:
        raise RuntimeError(f"Core Portal at {robot}:12000 did not return a valid state: {response}")
    if result.get("error") or result.get("error_message"):
        raise RuntimeError(f"Core Portal reports an error: {result.get('error') or result.get('error_message')}")
    if result.get("current_task") != "IdleTask":
        raise RuntimeError(f"Core is busy with {result.get('current_task')!r}; finish that task before learning.")
    if "control_active" not in result:
        raise RuntimeError("Core does not report controller readiness; rebuild the Core image before learning.")
    if result.get("status") != "Idle" or result["control_active"] is not False:
        raise RuntimeError(f"Core is not ready for learning: status={result.get('status')!r}.")
    try:
        with ServerProxy(f"http://{robot}:{service_port}", allow_none=True,
                         transport=_ServiceTransport()) as service:
            busy = service.is_busy()
    except Exception as error:
        raise RuntimeError(f"Cannot query the ML service at {robot}:{service_port}: {error}") from error
    if busy is not False:
        raise RuntimeError(f"ML service at {robot}:{service_port} is busy or returned an invalid state: {busy!r}")


def stop_learning(robot: str):
    """Stop further learning and the current Core task after an interrupted run."""
    deadline = time.monotonic() + 10
    while True:
        errors = []
        try:
            with ServerProxy(f"http://{robot}:8000", allow_none=True,
                             transport=_ServiceTransport()) as service:
                service.stop_service()
        except Exception as error:
            errors.append(f"ML stop request failed: {error}")
        try:
            call_method(robot, 12000, "stop_task",
                        {"raise_exception": False, "recover": False, "empty_queue": True},
                        timeout=5, open_timeout=5, close_timeout=0.2)
        except Exception as error:
            errors.append(f"Core stop request failed: {error}")
        # The stop replies precede worker shutdown. Retry while ML/Core are
        # busy, including when initialization raced the first stop request.
        # Core releases its controller when the current task stops.
        try:
            check_learning_services(robot, 8000)
            return
        except Exception as error:
            if time.monotonic() >= deadline:
                errors.append(f"Could not confirm learning stopped: {error}")
                raise RuntimeError("; ".join(errors)) from error
            time.sleep(0.2)


def example_learning(robot: str = "127.0.0.1", insertable="janinetest1"):
    tasks = {robot: insertable}
    check_learning_services(robot, 8000)
    check_taught_insertion_objects(robot, insertable)
    for host, insertable in tasks.items():
        container = insertable + "_container"
        approach = container + "_approach"
        
        # configuring the learning problem (problem definition):
        # for every skill there is a definition class (eg InsertionFactory) that creates the problem_definition
        # input: list of agents (usually one robot -> IP of mios)
        #        cost function: see from definitions.cost_functions, eg.: TimeMetric (skill_class, max_time, heuristic=np.exp(var)")
        #        objects: for insertion: insertable, pose when insertable is inserted, pose when insertable is above the container
        pd = InsertionFactory([host], TimeMetric("insertion", {"time": 15}),
                            {"Insertable": insertable, "Container": container,
                            "Approach": approach}).get_problem_definition(insertable)
        configure_supervised_motion(pd)
        pd.variate_only_success = True  # repeat trial only when successful
        # Try each candidate once
        pd.n_variations = 1
        pd.host = host  # host (only for ducumentation)
        pd.optimum_thr = 0.3  # trial is taged as optimal when cost is under this threshold 
        pd.cost_function.finish_thr = 2  # learning is finished when this threshold is reached with optimal trials; if exploration mode of the learning service is True, learning will still contiue

        # Leaning Service configuration:
        # For Example: SVMLearner (https://proceedings.mlr.press/v155/voigt21a/voigt21a.pdf)
        # inputs: max trials
        #         batch size
        #         number of immigrants (old way of sharing knowledge; not used right now, keep it to 0)
        #         exploration mode: whether the learner should contiue optimizing after finding a solution
        #         batch synchronization: only used in a multi robot setup when all robots should start a batch at the same time; not need -> keep it to False
        #         request probability: new way of sharing knowledge - defines the probability for the ml_service to request knowledge from other agents instead of creating a new trial itself.
        #                              0.4 is a good probability in multi robot systems
        #         request_probability_decrease: whether the request probability should be automaticcly adapt to success rate (True) or be keept steady (False)
        # Run a small supervised learning sequence one physical candidate at
        # a time. The batch width remains one, so the service cannot launch a
        # group of arm motions concurrently.
        sc = SVMLearner(5, 1, 0, True, False, -1, True).get_configuration()
        
        # Knowledge source definition:
        # all information regarding where to find knowledge and kind of knowledge should be used
        # mode = mode  # either None, "specific", "local", "global"     (if "None", but parameters is not empty, the parameters will be used as centroid)
        # type = type  # also possible: "predicted" (use prediction), "all" (gives list of knowledges, no predicted ones),
        # scope = scope  # scope (tags of results to make this knowledge)
        # kb_location = kb_location  # location of the knowledge base
        # kb_db = kb_db  # needed if type is specific
        # kb_task_type = kb_task_type  # needed if type is specific
        # parameters = parameters #dict() with unnormalised Theta
        # confidence = confidence
        # uuid = uuid   # single uuid or list of uuids
        # prediction = prediction  # bool, wether this knowledge was predicted or not
        # prediction_error = prediction_error
        # identity = identity  # task identity
        # skill_class = skill_class  # eg. "insertion"
        # skill_instance = skill_instance  #  skill_instance from problem_definition
        # source = source  # uuid(s) of the source ml_results
        # expected_cost = expected_cost
        # time = time  # time when knowledge point was created (time.time())
        # datetime = datetime  # time.ctime()
        # tags = tags  #actual tags of the knowledge itself
        # equal_start = equal_start  # if True the svm.py will use the same first batch (from equal_tags) every time
        # equal_tags = equal_tags
        # cost_function = cost_function
        # identification_name = identification_name  # identification string, because uuid is random
        # time_range = time_range  # time window from which knowledge can be collected to create new knowledge points
        # similarity = similarity  # list of objects with request probabilities
        # The first physical trial validates the pose that was just taught.
        # Seed SVM at the nominal domain point rather than drawing a random
        # orientation/contact-approach perturbation.
        knowledge = supervised_nominal_knowledge(pd)

        # this is a list of tags to find the entries on the mongoDB; 
        # the experiment wizard will append also some information here
        tags = ["example_learning", "tutorial"]  
        
        # helper function (experiment wizard):
        # mios IP
        # problem definition
        # service configuration
        # tags
        # knowledge source dict
        # number of iterations: how often should this experiment be repeated
        # service port: 8000
        # whether the function should return immediately or wait until learning is finished 

        learning_attempted = False
        try:
            set_active_grasped_object(host, insertable)
            learning_attempted = True  # A lost dispatch reply may still start ML.
            learn_task(host, pd, sc, tags, knowledge=knowledge, n_iterations=1,
                       service_port=8000, wait=True)
            check_learning_services(host, 8000)
        except BaseException:
            if learning_attempted:
                stop_learning(host)
            raise


        
def stop_services(robots:list = ["localhost"]):
    for r in robots:
        s = ServerProxy("http://" + r + ":8000", allow_none=True)
        try:
            s.stop_service()
        except Exception as e:
            print("Error with robot ",r)
            print(e)


if __name__ == "__main__":
    example_learning("127.0.0.1", "janinetest1")
