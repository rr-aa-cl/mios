#pragma once

#include "nlohmann/json.hpp"
#include "pybind11/pybind11.h"
#include "pybind11/embed.h"

namespace mios{

class LearningModule{
public:
    LearningModule();
    ~LearningModule();
    std::string learn_task(const nlohmann::json& problem_definition, const nlohmann::json& service_configuration, const nlohmann::json& agents);
    bool stop_learning(const std::string& uuid);

private:
    pybind11::object m_ml_interface;
};

}
