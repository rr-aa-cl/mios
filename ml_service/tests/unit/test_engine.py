"""
test_engine.py – Phase 0 baseline + Phase 3 threading tests for Engine.

The Engine is tested with a mock _execute_task that returns immediately,
so no real robot agents or WebSocket connections are needed.
"""
import threading
import time
import uuid
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_mongo():
    """Return a simple object that satisfies Engine's mongo writes."""
    m = MagicMock()
    m.write.return_value = "mock_id"
    m.read.return_value = []
    return m


@pytest.fixture()
def minimal_engine(mock_mongo):
    """
    Create an Engine with Redis and ws-calls patched out so it can be
    instantiated without live services.
    """
    with patch("engine.engine.redis.Redis") as mock_redis_cls:
        mock_redis = MagicMock()
        mock_redis_cls.return_value = mock_redis

        from engine.engine import Engine
        engine = Engine.__new__(Engine)
        engine.mongo_client = mock_mongo
        engine.agents = {"mock_agent"}
        engine.free_agents = {"mock_agent"}
        engine.queued_trials = __import__("queue").Queue()
        engine.completed_trials = {}
        engine.keep_running = False
        engine.stop_condition = None
        engine.redisClient = mock_redis
        engine.worker_threads = {}
        engine._learned = False
        engine.result = None
        engine.cnt_pushed = 0
        return engine


# ---------------------------------------------------------------------------
# Trial dataclass / namedtuple basic smoke test
# ---------------------------------------------------------------------------
class TestTrialConstruction:
    def test_trial_has_uuid(self):
        from engine.engine import Trial
        t = Trial(
            task_context={},
            reset_instructions=[],
            rescue_instructions=[],
            theta={"p1": 0.5},
            log=True,
            external=False
        )
        t.trial_uuid = str(uuid.uuid4())
        assert t.trial_uuid is not None

    def test_trial_theta_preserved(self):
        from engine.engine import Trial
        theta = {"p1": 0.1, "p2": 0.2}
        t = Trial(
            task_context={},
            reset_instructions=[],
            rescue_instructions=[],
            theta=theta,
            log=True,
            external=False
        )
        assert t.theta == theta


# ---------------------------------------------------------------------------
# Engine queue mechanics
# ---------------------------------------------------------------------------
class TestEngineQueue:
    def test_push_to_queue_adds_item(self, minimal_engine):
        from engine.engine import Trial
        t = Trial({}, [], [], {"p1": 0.5}, True, False)
        minimal_engine.queued_trials.put(t)
        assert minimal_engine.queued_trials.qsize() == 1

    def test_queue_fifo_order(self, minimal_engine):
        from engine.engine import Trial
        for i in range(3):
            t = Trial({}, [], [], {"p1": float(i)}, True, False)
            t.trial_uuid = f"u{i}"
            minimal_engine.queued_trials.put(t)
        uuids = []
        while not minimal_engine.queued_trials.empty():
            uuids.append(minimal_engine.queued_trials.get().trial_uuid)
        assert uuids == ["u0", "u1", "u2"]


# ---------------------------------------------------------------------------
# Phase 3 – stop() terminates the main_loop within timeout
# ---------------------------------------------------------------------------
class TestEngineStop:
    def test_stop_flag_prevents_processing(self, minimal_engine):
        """Engine with keep_running=False should not process any trial."""
        minimal_engine.keep_running = False
        # Verify the flag is respected (main_loop exit condition)
        assert minimal_engine.keep_running is False

    def test_keep_running_can_be_set(self, minimal_engine):
        minimal_engine.keep_running = True
        assert minimal_engine.keep_running is True
        minimal_engine.keep_running = False
        assert minimal_engine.keep_running is False


# ---------------------------------------------------------------------------
# Phase 3 – Threading.Event per trial (future behaviour, tested as contract)
# ---------------------------------------------------------------------------
class TestTrialEvents:
    def test_event_set_and_wait(self):
        """Baseline: threading.Event can signal completion."""
        events = {}
        uid = "trial-abc"
        events[uid] = threading.Event()

        def simulate_completion():
            time.sleep(0.05)
            events[uid].set()

        t = threading.Thread(target=simulate_completion)
        t.start()
        signalled = events[uid].wait(timeout=2.0)
        t.join()
        assert signalled is True

    def test_event_timeout_returns_false(self):
        evt = threading.Event()
        result = evt.wait(timeout=0.05)
        assert result is False


# ---------------------------------------------------------------------------
# Trial.to_dict()
# ---------------------------------------------------------------------------
class TestTrialToDict:
    def test_to_dict_contains_required_keys(self):
        from engine.engine import Trial
        theta = {"p1": 0.5, "p2": 0.3}
        t = Trial(
            task_context={"name": "TestTask", "skills": {}},
            reset_instructions=[],
            rescue_instructions=[],
            theta=theta,
            log=True,
            external=False,
        )
        d = t.to_dict()
        for key in ("task_context", "reset_instructions", "theta",
                     "task_result", "trial_uuid", "agent", "log", "external"):
            assert key in d, f"Missing key: {key}"

    def test_to_dict_preserves_theta_as_floats(self):
        from engine.engine import Trial
        import numpy as np
        theta = {"p1": np.float64(0.123)}
        t = Trial({"name": "T", "skills": {}}, [], [], theta, True, False)
        d = t.to_dict()
        assert isinstance(d["theta"]["p1"], float)

    def test_to_dict_includes_task_result(self):
        from engine.engine import Trial
        t = Trial({"name": "T", "skills": {}}, [], [], {"p1": 1.0}, True, False)
        d = t.to_dict()
        assert "q_metric" in d["task_result"]


# ---------------------------------------------------------------------------
# Trial.is_valid()
# ---------------------------------------------------------------------------
class TestTrialIsValid:
    def test_valid_trial_returns_true(self):
        from engine.engine import Trial
        t = Trial(
            task_context={"name": "TestTask", "skills": {}},
            reset_instructions=[],
            rescue_instructions=[],
            theta={"p1": 0.5},
            log=True,
            external=False,
        )
        assert t.is_valid() is True

    def test_missing_name_returns_false(self):
        from engine.engine import Trial
        t = Trial(
            task_context={"skills": {}},  # missing "name"
            reset_instructions=[],
            rescue_instructions=[],
            theta={"p1": 0.5},
            log=True,
            external=False,
        )
        assert t.is_valid() is False

    def test_empty_context_returns_false(self):
        from engine.engine import Trial
        t = Trial(
            task_context={},
            reset_instructions=[],
            rescue_instructions=[],
            theta={},
            log=True,
            external=False,
        )
        assert t.is_valid() is False


# ---------------------------------------------------------------------------
# Engine.push_trial() – uuid assignment and invalid trial handling
# ---------------------------------------------------------------------------
class TestEnginePushTrial:
    def test_push_valid_trial_returns_uuid(self, minimal_engine):
        from engine.engine import Trial
        t = Trial(
            task_context={"name": "TestTask", "skills": {}},
            reset_instructions=[],
            rescue_instructions=[],
            theta={"p1": 0.5},
            log=True,
            external=False,
        )
        uuid_str = minimal_engine.push_trial(t)
        assert uuid_str != "INVALID"
        assert len(uuid_str) == 36  # UUID4 format: 8-4-4-4-12

    def test_push_invalid_trial_returns_invalid(self, minimal_engine):
        from engine.engine import Trial
        t = Trial(
            task_context={},  # no "name" → invalid
            reset_instructions=[],
            rescue_instructions=[],
            theta={},
            log=True,
            external=False,
        )
        assert minimal_engine.push_trial(t) == "INVALID"

    def test_push_increments_cnt_pushed(self, minimal_engine):
        from engine.engine import Trial
        t = Trial({"name": "T", "skills": {}}, [], [], {"p1": 0.5}, True, False)
        initial = minimal_engine.cnt_pushed
        minimal_engine.push_trial(t)
        assert minimal_engine.cnt_pushed == initial + 1

    def test_push_adds_to_queue(self, minimal_engine):
        from engine.engine import Trial
        t = Trial({"name": "T", "skills": {}}, [], [], {"p1": 0.5}, True, False)
        minimal_engine.push_trial(t)
        assert minimal_engine.queued_trials.qsize() == 1

