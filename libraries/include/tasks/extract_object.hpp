#pragma once

#include "task/task.hpp"

namespace mios{
class ExtractObject : public Task{
public:
    ExtractObject(Core* core);
    void initialize_context() override;
    void execute() override;
    bool read_parameters(const nlohmann::json& params) override;
    void get_default_context(nlohmann::json &context) override;

private:

    std::string m_extractable;
    std::string m_extract_from;
    std::string m_extract_to;

};
}
