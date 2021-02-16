#pragma once

#include "task/task.hpp"
#include <vector>
#include <string>

namespace mios {

class GenericTask : public Task{
public:
    GenericTask(Core* core);

    void initialize_context() override;
    void execute() override;
    bool read_parameters(const nlohmann::json &params) override;
    void get_default_context(nlohmann::json &context) override;

private:
    void execute_any_skill(unsigned index);
    void add_any_skill(unsigned index);

private:
    std::vector<std::pair<std::string,std::string> > m_skills;
    bool m_as_queue;
};

}
