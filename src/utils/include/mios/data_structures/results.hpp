#pragma once

#include "mios/data_structures/percept.hpp"
#include "nlohmann/json.hpp"

#include <string>
#include <unordered_map>

namespace mios {

struct SkillCost{
    SkillCost(){
        time=0;
        contact_forces=0;
        custom=0;
        effort_avg=0;
        effort_total=0;
        distance=0;
    }
    nlohmann::json to_json() const{
        nlohmann::json cost;
        cost["time"]=time;
        cost["contact_forces"]=contact_forces;
        cost["effort_avg"]=effort_avg;
        cost["effort_total"]=effort_total;
        cost["distance"]=distance;
        cost["custom"]=custom;
        return cost;
    }
    double time;
    double contact_forces;
    double effort_avg;
    double effort_total;
    double distance;
    double custom;
};

struct SkillResult{
public:
    SkillResult(){
        cost=SkillCost();
        heuristic=0;
        success=false;
        last_errors.resize(0);
        results=nlohmann::json();
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
    SkillCost cost;

    /**
     * Cost of skill execution in case of failure.
     */
    double heuristic;

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
        success=false;
        external_stop=false;
        exception=false;
        empty_queue=false;
        custom_results=nlohmann::json();
        errors.resize(0);
    }

    std::unordered_map<std::string,SkillResult> skill_results;

    bool success;
    bool external_stop;
    bool exception;
    bool empty_queue;
    nlohmann::json custom_results;
    std::vector<std::string> errors;
};

}
