"""Exercise the actual queue-cancellation method without Core or robot services."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("g++"), "g++ is required")
class TaskCancellationTests(unittest.TestCase):
    def test_stop_cancels_queued_start_and_releases_lock_before_worker_wait(self):
        source = (ROOT / "src/task/src/task_engine.cpp").read_text()
        method = source[source.index("std::pair<bool,std::string> TaskEngine::stop_task("):
                        source.index("std::pair<bool,std::string> TaskEngine::remove_task(")]
        harness = r'''
#include <cassert>
#include <future>
#include <list>
#include <memory>
#include <mutex>
#include <string>
#include <tuple>
#include <utility>
namespace spdlog { void info(const char*) {} }
struct Task {
  std::string id;
  std::mutex* queue_mutex;
  bool stopped = false;
  bool emptied = false;
  std::string get_id() const { return id; }
  void stop_task(bool, bool, bool empty) {
    // Model a worker needing the queue while the caller waits for shutdown.
    auto worker = std::async(std::launch::async, [this] {
      assert(queue_mutex->try_lock());
      queue_mutex->unlock();
    });
    worker.get();
    stopped = true;
    emptied = empty;
  }
};
struct TaskEngine {
  std::mutex m_mtx_task_queue;
  std::shared_ptr<Task> m_active_task;
  std::list<std::tuple<std::string, std::shared_ptr<Task>, int>> m_task_queue;
  std::pair<bool, std::string> stop_task(bool, bool, bool);
  std::shared_ptr<Task> task(const std::string& id) {
    auto t = std::make_shared<Task>(Task{id, &m_mtx_task_queue});
    m_task_queue.emplace_back(id, t, 0);
    return t;
  }
};
'''
        cases = r'''
int main() {
  {
    TaskEngine engine;
    engine.m_active_task = engine.task("IdleTask");
    auto queued = engine.task("HandGuiding");
    assert(engine.stop_task(false, false, true).first);
    assert(engine.m_task_queue.size() == 1);
    assert(std::get<1>(engine.m_task_queue.front()) == engine.m_active_task);
    assert(!queued->stopped && !engine.m_active_task->stopped);
  }
  {
    TaskEngine engine;
    engine.m_active_task = engine.task("HandGuiding");
    engine.task("NextMotion");
    assert(engine.stop_task(false, false, true).first);
    assert(engine.m_task_queue.size() == 1);
    assert(engine.m_active_task->stopped && engine.m_active_task->emptied);
  }
  {
    TaskEngine engine;
    engine.m_active_task = engine.task("IdleTask");
    engine.task("PendingMotion");
    assert(engine.stop_task(false, false, false).first);
    assert(engine.m_task_queue.size() == 2);
  }
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "test.cpp").write_text(harness + method + cases)
            subprocess.run(["g++", "-std=c++17", "-pthread", str(path / "test.cpp"),
                            "-o", str(path / "test")], check=True, capture_output=True, timeout=30)
            subprocess.run([str(path / "test")], check=True, capture_output=True, timeout=5)


if __name__ == "__main__":
    unittest.main()
