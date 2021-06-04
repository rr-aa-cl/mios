#pragma once

#include <unordered_map>
#include <string>
#include <nlohmann/json.hpp>

#include "data_structures/results.hpp"

namespace mios {

struct TaskData{
    TaskData():name("NullData"),context(nlohmann::json()){

    }
    TaskData(const std::string& name, const nlohmann::json& context, const TaskResult& result):name(name),context(context),result(result){

    }
    std::string name;
    nlohmann::json context;
    TaskResult result;
};

}
