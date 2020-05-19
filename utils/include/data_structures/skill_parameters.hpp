#pragma once

#include <unordered_map>
#include <string>
#include <nlohmann/json.hpp>

namespace mios {

struct SkillParameters{
    SkillParameters(){
        common.time_max=0;
        common.w_cost_function.resize(10);
        common.w_cost_function[0]=1;
        common.parallels_frequency=1;
    }

    /**
     * Reads common skill parameters into the local configuration struct.
     * @param[in] p Common skill parameters in json format.
     */
    void read_global_skill_parameters(const nlohmann::json& p);
    virtual bool read_parameters(const nlohmann::json& parameters) = 0;

    struct Common{
        /**
         * Mapping of skill objects to objects in the knowledge base.
         */
        std::unordered_map<std::string,std::string> objects;

        /**
         * Maximum time for skill execution. After exceeding this time the skill is terminated unsuccessful. A value of 0 allows for infinite execution time.
         */
        double time_max;

        /**
         * Id to select a custom cost function.
         */
        std::vector<double> w_cost_function;

        /**
         * Frequency of parallel thread
         */
        unsigned parallels_frequency;

    }common;
};

}
