#pragma once

#include <string>
#include <mutex>

namespace mios {

class TaskObserver{
public:
    TaskObserver();
    ~TaskObserver();

    void wait_for_finish();
    void finish();
    std::string get_id();
private:
    std::mutex m_finished;
};

}
