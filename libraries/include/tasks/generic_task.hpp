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
    void evaluate() override;
    bool read_parameters(const nlohmann::json &params) override;

private:
    void execute_any_skill(unsigned index);

private:
    std::vector<std::pair<std::string,std::string> > m_skills;
};

}
