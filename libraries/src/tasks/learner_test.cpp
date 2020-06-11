#include "tasks/learner_test.hpp"
#include "skills/ml_test_skill.hpp"

namespace mios{

LearnerTest::LearnerTest(Core *core):Task("LearnerTest",core){
}

void LearnerTest::initialize_context(){
    reserve_skill("ml_test");
}

void LearnerTest::execute(){
    execute_skill<MLTestSkill,SkillParametersMLTestSkill>("ml_test");
}
void LearnerTest::evaluate(){
    write_result(get_result().skill_results["ml_test"].success,get_result().skill_results["ml_test"].cost_suc,get_result().skill_results["ml_test"].cost_err,get_result().skill_results["ml_test"].results);
}

bool LearnerTest::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param<double,6,1>(params,"x",m_x)){
        spdlog::error("Missing parameter: x [6x1]");
        return false;
    }
    return true;
}

}
