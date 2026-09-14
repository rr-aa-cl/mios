"""Offline checks for factory learning defaults and the nominal first seed."""

import contextlib
import copy
import unittest
from unittest import mock

import numpy as np

from definitions.cost_functions import TimeMetric
from definitions.templates import InsertionFactory
from services.base_service import BaseService
import example_learning as examples


def _insertion_problem_definition():
    return InsertionFactory(["127.0.0.1"], TimeMetric("insertion", {"time": 15}), {
        "Insertable": "samuelnew",
        "Container": "samuelnew_container",
        "Approach": "samuelnew_container_approach",
    }).get_problem_definition("samuelnew")


def test_supervised_first_trial_is_the_nominal_taught_baseline():
    problem_definition = _insertion_problem_definition()
    knowledge = examples.supervised_nominal_knowledge(problem_definition)
    parameters = knowledge["parameters"]

    assert list(parameters) == problem_definition.domain.vector_mapping
    assert knowledge["meta"]["mode"] is None
    assert knowledge["meta"]["confidence"] == 0.0
    assert parameters["p0_offset_x"] == 0.0
    assert parameters["p0_offset_y"] == 0.0
    assert parameters["p0_offset_phi"] == 0.0
    assert parameters["p0_offset_chi"] == 0.0
    for parameter, value in parameters.items():
        lower, upper = problem_definition.domain.limits[parameter]
        assert type(value) is float
        assert lower <= value <= upper
    assert np.isclose(parameters["p1_dx_d"], 0.02)
    assert parameters["p1_K_x"] == 200.0
    assert parameters["p2_f_push_z"] == 2.0


def test_first_contact_seed_changes_only_contact_speed_without_mutating_factory():
    problem_definition = _insertion_problem_definition()
    domain_before = copy.deepcopy(problem_definition.domain.to_dict())
    contexts_before = copy.deepcopy((
        problem_definition.default_context,
        problem_definition.setup_instructions,
        problem_definition.reset_instructions,
        problem_definition.rescue_instructions,
        problem_definition.termination_instructions,
    ))
    expected_x0 = problem_definition.domain.get_default_x0().copy()
    expected_x0[problem_definition.domain.vector_mapping.index("p1_dx_d")] = 0.2

    knowledge = examples.supervised_nominal_knowledge(problem_definition)
    physical = np.asarray(list(knowledge["parameters"].values()))
    normalized = problem_definition.domain.normalize(physical)

    np.testing.assert_allclose(normalized, expected_x0, rtol=0, atol=1e-12)
    assert problem_definition.domain.to_dict() == domain_before
    assert (
        problem_definition.default_context,
        problem_definition.setup_instructions,
        problem_definition.reset_instructions,
        problem_definition.rescue_instructions,
        problem_definition.termination_instructions,
    ) == contexts_before


def test_first_contact_seed_reaches_the_mapped_trial_context():
    problem_definition = _insertion_problem_definition()
    knowledge = examples.supervised_nominal_knowledge(problem_definition)
    physical = np.asarray(list(knowledge["parameters"].values()))
    normalized = problem_definition.domain.normalize(physical)
    trial_values = problem_definition.domain.denormalize(normalized)

    # Exercise the service's real mapping without constructing its DB clients
    # or engine. The service applies candidate values to its own context copy.
    service = mock.Mock(problem_definition=copy.deepcopy(problem_definition))
    service.set_nested_parameter.side_effect = lambda *args: BaseService.set_nested_parameter(service, *args)
    context = BaseService.update_default_context(service, trial_values)

    insertion = context["skills"]["insertion"]["skill"]
    assert np.isclose(insertion["p1"]["dX_d"][0], 0.02)
    assert np.isclose(insertion["p1"]["dX_d"][1], 0.05)
    assert insertion["p1"]["K_x"] == [200.0, 200.0, 200.0, 20.0, 20.0, 20.0]
    assert insertion["p0"] == problem_definition.default_context["skills"]["insertion"]["skill"]["p0"]
    assert problem_definition.default_context["skills"]["insertion"]["skill"]["p1"]["dX_d"] == [0.1, 0.5]


def test_first_contact_seed_rejects_speed_outside_the_problem_domain():
    problem_definition = _insertion_problem_definition()
    problem_definition.domain.limits["p1_dx_d"] = (0.0, 0.015)
    before = copy.deepcopy(problem_definition.domain.to_dict())

    with unittest.TestCase().assertRaises(ValueError):
        examples.supervised_nominal_knowledge(problem_definition)

    assert problem_definition.domain.to_dict() == before


def _assert_motion_profiles(problem_definition, original):
    observed_moves = []
    observed_extractions = []
    for group in ("setup_instructions", "reset_instructions", "rescue_instructions", "termination_instructions"):
        instructions = getattr(problem_definition, group)
        originals = getattr(original, group)
        assert len(instructions) == len(originals)
        for instruction, original_instruction in zip(instructions, originals):
            context = instruction["parameters"]
            restored_instruction = copy.deepcopy(instruction)
            parameters = context["parameters"]
            for name, skill_type in zip(parameters["skill_names"], parameters["skill_types"]):
                skill = context["skills"][name]
                original_skill = original_instruction["parameters"]["skills"][name]
                restored = restored_instruction["parameters"]["skills"][name]
                if skill_type == "MoveToPoseJoint":
                    observed_moves.append((group, name))
                    assert skill["control"]["control_mode"] == 1
                    assert skill["skill"]["speed"] == (0.10 if group == "setup_instructions" else 0.05)
                    assert skill["skill"]["acc"] == (0.20 if group == "setup_instructions" else 0.10)
                    restored["control"]["control_mode"] = original_skill["control"]["control_mode"]
                    for parameter in ("speed", "acc"):
                        restored["skill"][parameter] = original_skill["skill"][parameter]
                elif skill_type == "TaxExtraction":
                    observed_extractions.append((group, name))
                    assert skill["control"]["control_mode"] == 0
                    for phase in ("p0", "p1"):
                        assert skill["skill"][phase]["dX_d"] == [0.02, 0.1]
                        assert skill["skill"][phase]["ddX_d"] == [0.1, 0.2]
                        for parameter in ("dX_d", "ddX_d"):
                            restored["skill"][phase][parameter] = original_skill["skill"][phase][parameter]
            # Object names, stiffness, damping, modes, and unrelated skill/task
            # settings must be identical outside the intended motion changes.
            assert restored_instruction == original_instruction
    return observed_moves, observed_extractions


def test_motion_profiles_cover_return_and_termination_skills():
    problem_definition = _insertion_problem_definition()
    # The insertion factory currently has no termination instructions. Reuse
    # a real mixed extraction/joint-return instruction to cover that path too.
    problem_definition.termination_instructions = copy.deepcopy(problem_definition.reset_instructions)
    original = copy.deepcopy(problem_definition)

    examples.configure_supervised_motion(problem_definition)

    moves, extractions = _assert_motion_profiles(problem_definition, original)
    assert ("termination_instructions", "move_approach") in moves
    assert ("termination_instructions", "extraction") in extractions
    assert problem_definition.domain.to_dict() == original.domain.to_dict()
    assert problem_definition.default_context == original.default_context


def test_learning_dispatch_preserves_factory_ranges_and_p0_with_effort_joint_moves():
    original = _insertion_problem_definition()
    with contextlib.ExitStack() as stack:
        for name in ("check_learning_services", "check_taught_insertion_objects",
                     "set_active_grasped_object"):
            stack.enter_context(mock.patch.object(examples, name))
        learn = stack.enter_context(mock.patch.object(examples, "learn_task"))
        for name in ("call_method", "ServerProxy", "start_experiment"):
            stack.enter_context(mock.patch.object(
                examples, name, side_effect=AssertionError("Unexpected external operation")))

        examples.example_learning("127.0.0.1", "samuelnew")

    learn.assert_called_once()
    problem_definition = learn.call_args.args[1]
    configuration = learn.call_args.args[2]
    assert problem_definition.domain.to_dict() == original.domain.to_dict()
    assert problem_definition.domain.limits["p0_offset_x"] == (-0.005, 0.005)
    assert problem_definition.domain.limits["p1_dx_d"] == (0, 0.1)
    assert problem_definition.domain.limits["p2_f_push_z"] == (0, 20)
    assert problem_definition.default_context == original.default_context
    p0 = problem_definition.default_context["skills"]["insertion"]["skill"]["p0"]
    assert p0["dX_d"] == [0.1, 1]
    assert p0["ddX_d"] == [0.5, 4]

    moves, extractions = _assert_motion_profiles(problem_definition, original)
    assert moves == [("setup_instructions", "move"),
                     ("reset_instructions", "move_approach"),
                     ("rescue_instructions", "move_back")]
    assert extractions == [("reset_instructions", "extraction")]
    assert learn.call_args.kwargs["knowledge"]["parameters"]["p1_dx_d"] == 0.02
    assert configuration.n_trials == 5
    assert configuration.batch_width == 1
    assert problem_definition.n_variations == 1
    assert learn.call_args.kwargs["n_iterations"] == 1
    assert learn.call_args.kwargs["wait"] is True
