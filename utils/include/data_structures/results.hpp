#pragma once

#include "data_structures/percept.hpp"
#include <unordered_map>
#include <string>
#include <nlohmann/json.hpp>

namespace mios {

struct SkillResult{
public:
    SkillResult(){
        this->cost_suc=0;
        this->cost_err=0;
        this->success=false;
        this->last_errors.resize(0);
        this->results=nlohmann::json();
        exception=false;
    }
    /**
     * Map that contains the percept struct at the beginning of execution of each manipulation primitive of the skill.
     * The key is the name of the respective primitive.
     */
    std::unordered_map<std::string,Percept> percepts;

    /**
     * Percept struct at the beginning of skill execution.
     */
    Percept p_0;

    /**
     * Percept struct at the end of skill execution.
     */
    Percept p_1;

    /**
     * Cost of skill execution in case of success.
     */
    double cost_suc;

    /**
     * Cost of skill execution in case of failure.
     */
    double cost_err;

    /**
     * Additional inquality constraints. The key is the constraint's identifier, the value the constraint in implicit form.
     */
    std::unordered_map<std::string,double> constraints;

    /**
     * Indicates whether the skill execution was successful.
     */
    bool success;

    bool exception;

    /**
     * Lists the last thrown exceptions.
     */
    std::vector<std::string> last_errors;

    nlohmann::json results;

};

struct TaskResult{
    /**
     * The constructor of the struct is by default called to build a nominal, unsuccessful task evaluation.
     * @param nominal
     */
    TaskResult(){
        cost_suc=0;
        cost_err=0;
        success=false;
        exception=false;
        empty_queue=false;
        custom_results=nlohmann::json();
        errors.resize(0);
    }

    std::unordered_map<std::string,SkillResult> m_skill_results;

    double cost_suc;
    double cost_err;
    bool success;
    bool exception;
    bool empty_queue;
    nlohmann::json custom_results;
    std::vector<std::string> errors;
};

}
