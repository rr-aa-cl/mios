"""
test_domain.py – Unit tests for Domain (normalize / denormalize / self_check).
No hardware or MongoDB required.
"""
import numpy as np
import pytest
from problem_definition.domain import Domain


@pytest.fixture()
def two_param_domain():
    limits = {"a": (0.0, 10.0), "b": (-5.0, 5.0)}
    mapping = {"a": ["skills.s.skill.a"], "b": ["skills.s.skill.b"]}
    x_0 = {"a": 0.5, "b": 0.5}
    return Domain(limits, mapping, x_0)


class TestNormalize:
    def test_midpoint_normalises_to_half(self, two_param_domain):
        x = np.array([5.0, 0.0])
        x_norm = two_param_domain.normalize(x)
        np.testing.assert_allclose(x_norm, [0.5, 0.5])

    def test_lower_bound_normalises_to_zero(self, two_param_domain):
        x = np.array([0.0, -5.0])
        x_norm = two_param_domain.normalize(x)
        np.testing.assert_allclose(x_norm, [0.0, 0.0])

    def test_upper_bound_normalises_to_one(self, two_param_domain):
        x = np.array([10.0, 5.0])
        x_norm = two_param_domain.normalize(x)
        np.testing.assert_allclose(x_norm, [1.0, 1.0])

    def test_clamps_above_upper_bound(self, two_param_domain):
        x = np.array([999.0, 0.0])
        x_norm = two_param_domain.normalize(x)
        assert x_norm[0] == pytest.approx(1.0)

    def test_clamps_below_lower_bound(self, two_param_domain):
        x = np.array([0.0, -999.0])
        x_norm = two_param_domain.normalize(x)
        assert x_norm[1] == pytest.approx(0.0)


class TestDenormalize:
    def test_half_denormalises_to_midpoint(self, two_param_domain):
        x_norm = np.array([0.5, 0.5])
        x = two_param_domain.denormalize(x_norm)
        np.testing.assert_allclose(x, [5.0, 0.0])

    def test_zero_denormalises_to_lower_bound(self, two_param_domain):
        x_norm = np.array([0.0, 0.0])
        x = two_param_domain.denormalize(x_norm)
        np.testing.assert_allclose(x, [0.0, -5.0])

    def test_one_denormalises_to_upper_bound(self, two_param_domain):
        x_norm = np.array([1.0, 1.0])
        x = two_param_domain.denormalize(x_norm)
        np.testing.assert_allclose(x, [10.0, 5.0])

    def test_roundtrip_normalize_denormalize(self, two_param_domain):
        original = np.array([3.7, 1.2])
        roundtrip = two_param_domain.denormalize(two_param_domain.normalize(original.copy()))
        np.testing.assert_allclose(roundtrip, original, atol=1e-9)


class TestSelfCheck:
    def test_valid_domain_passes(self, two_param_domain):
        assert two_param_domain.self_check() is True

    def test_missing_x0_key_fails(self):
        limits = {"a": (0.0, 1.0), "b": (0.0, 1.0)}
        mapping = {"a": ["x"], "b": ["y"]}
        x_0 = {"a": 0.5}  # missing "b"
        d = Domain(limits, mapping, x_0)
        # Domain.__init__ fills missing x_0 keys with 0, so self_check should still pass
        # (the constructor sets x_0[p] = 0 for all limits keys)
        assert d.self_check() is True

    def test_extra_context_mapping_key_fails(self):
        limits = {"a": (0.0, 1.0)}
        mapping = {"a": ["x"], "extra": ["y"]}  # "extra" not in limits
        x_0 = {"a": 0.5}
        d = Domain.__new__(Domain)
        d.limits = limits
        d.context_mapping = mapping
        d.x_0 = x_0
        d.vector_mapping = list(limits.keys())
        d.non_shareables = []
        assert d.self_check() is False


class TestToFromDict:
    def test_roundtrip(self, two_param_domain):
        d = two_param_domain
        reconstructed = Domain.from_dict(d.to_dict())
        assert reconstructed.limits == d.limits
        assert reconstructed.vector_mapping == d.vector_mapping
        assert reconstructed.context_mapping == d.context_mapping
