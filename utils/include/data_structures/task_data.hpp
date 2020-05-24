#pragma once

#include <unordered_map>
#include <string>
#include <nlohmann/json.hpp>

#include "data_structures/results.hpp"

namespace mios {

struct TaskData{
    nlohmann::json context;
    TaskResult result;
    std::string name;
};

}
