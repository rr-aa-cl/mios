#pragma once

#include "task/task.hpp"

namespace mios{
class InsertObject : public Task{
public:
    InsertObject(Core* core);
    void initialize_context() override;
    void execute() override;
    bool read_parameters(const nlohmann::json& params) override;
    void get_default_context(nlohmann::json &context) override;

private:

    std::string m_insertable;
    std::string m_insert_into;
    std::string m_insert_approach;
    Eigen::Matrix<double,6,1> m_offset;

};
}
