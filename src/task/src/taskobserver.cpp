#include "mios/task/taskobserver.hpp"

#include "spdlog/spdlog.h"

namespace mios {

TaskObserver::TaskObserver(){
    spdlog::trace("TaskOberserver::TaskObserver()");
    m_finished.lock();
}

TaskObserver::~TaskObserver(){
    spdlog::trace("TaskObserver::~TaskObserver()");
}

void TaskObserver::wait_for_finish(){
    std::scoped_lock<std::mutex> finish_lock(m_finished);
}

void TaskObserver::finish(){
    m_finished.unlock();
}

}
