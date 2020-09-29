#include "tasks/learner_test.hpp"
#include "skills/ml_test_skill.hpp"

namespace mios{

LearnerTest::LearnerTest(Core *core):Task("LearnerTest",core){
}

void LearnerTest::initialize_context(){
    reserve_skill("ml_test");
    overwrite_context("ml_test","skill","x",msrm_utils::from_eigen<double,6,1>(m_x));
    overwrite_context("ml_test","skill","weights",msrm_utils::from_eigen<double,2,1>(m_weights));
}

void LearnerTest::execute(){
    execute_skill<MLTestSkill,SkillParametersMLTestSkill>("ml_test");
}

bool LearnerTest::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param<double,6,1>(params,"x",m_x)){
        spdlog::error("Missing parameter: x [6x1]");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(params,"weights",m_weights)){
        m_weights<<1,0;
        return false;
    }
    return true;
}

void LearnerTest::get_default_context(nlohmann::json &context){
    context["parameters"] = nlohmann::json();
    context["parameters"]["x"]=nlohmann::json();
    context["parameters"]["weights"]=nlohmann::json();

    context["skills"]=nlohmann::json();
    context["skills"]["ml_test"]=nlohmann::json();
    context["skills"]["ml_test"]["control"]={{"control_mode",3}};
    context["skills"]["ml_test"]["type"]="MLTestSkill";
}

}
