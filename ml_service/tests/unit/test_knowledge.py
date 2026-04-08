"""
test_knowledge.py – Phase 0 baseline tests for the Knowledge class.
No hardware or MongoDB required.
"""
import pytest
import time as time_mod
from services.knowledge import Knowledge


class TestKnowledgeInit:
    def test_default_mode_is_none(self):
        k = Knowledge()
        assert k.mode is None

    def test_default_scope_is_empty_list(self):
        k = Knowledge()
        assert k.scope == []

    def test_custom_fields_set_correctly(self):
        k = Knowledge(mode="local", scope=["test"], confidence=0.8)
        assert k.mode == "local"
        assert k.scope == ["test"]
        assert k.confidence == 0.8


class TestKnowledgeToDict:
    def test_to_dict_has_parameters_and_meta(self):
        k = Knowledge(parameters={"p_x": 0.5})
        d = k.to_dict()
        assert "parameters" in d
        assert "meta" in d

    def test_to_dict_parameters_preserved(self):
        params = {"p_x": 0.5, "p_y": 0.3}
        k = Knowledge(parameters=params)
        assert k.to_dict()["parameters"] == params

    def test_to_dict_mode_in_meta(self):
        k = Knowledge(mode="global")
        assert k.to_dict()["meta"]["mode"] == "global"


class TestKnowledgeFromDict:
    def test_from_dict_restores_mode(self):
        k = Knowledge(mode="local", scope=["a"], skill_class="insertion")
        k.update()
        d = k.to_dict()
        k2 = Knowledge()
        k2.from_dict(d)
        assert k2.mode == "local"

    def test_from_dict_restores_scope(self):
        k = Knowledge(scope=["x", "y"])
        k.update()
        k2 = Knowledge()
        k2.from_dict(k.to_dict())
        assert k2.scope == ["x", "y"]

    def test_from_dict_restores_parameters(self):
        params = {"p_x": 0.1, "p_y": 0.9}
        k = Knowledge(parameters=params)
        k.update()
        k2 = Knowledge()
        k2.from_dict(k.to_dict())
        assert k2.parameters == params

    def test_roundtrip_time_range(self):
        k = Knowledge(time_range=(100.0, 500.0))
        k.update()
        k2 = Knowledge()
        k2.from_dict(k.to_dict())
        assert tuple(k2.time_range) == (100.0, 500.0)


class TestKnowledgeCheckConsistency:
    def test_global_mode_without_location_logs_error(self, caplog):
        import logging
        k = Knowledge(mode="global", kb_location=None)
        with caplog.at_level(logging.ERROR, logger="ml_service"):
            k.check_consistency()
        assert "kb_location" in caplog.text

    def test_valid_global_mode_no_error(self, caplog):
        import logging
        k = Knowledge(mode="global", kb_location="robot-01", type="similar")
        with caplog.at_level(logging.ERROR, logger="ml_service"):
            k.check_consistency()
        assert "kb_location" not in caplog.text


class TestGetIdentificationName:
    def test_includes_skill_class_and_instance(self):
        k = Knowledge(skill_class="insertion", skill_instance="cyl40", identity=[1], tags=["tag1"])
        name = k.get_identification_name()
        assert "insertion" in name
        assert "cyl40" in name
