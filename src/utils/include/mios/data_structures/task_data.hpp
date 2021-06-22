#pragma once

#include "mios/data_structures/results.hpp"
#include "nlohmann/json.hpp"

#include <unordered_map>
#include <string>


namespace mios {

struct TaskData{
    TaskData():name("NullData"),context(nlohmann::json()){

    }
    TaskData(const std::string& name_in, const nlohmann::json& context_in, const TaskResult& result_in):name(name_in),context(context_in),result(result_in){

    }
    std::string name;
    nlohmann::json context;
    TaskResult result;
};

}
