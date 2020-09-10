#include "tasks/test_task_2.hpp"
#include "tasks/test_task_1.hpp"
#include "skills/test_skill_1.hpp"
namespace mios{
TestTask2::TestTask2(Core* core):Task("TestTask2",core){
}
void TestTask2::initialize_context(){
    reserve_skill("t2_s1");
    reserve_skill("t2_s2");
    reserve_subtask("t2_t1");
}
void TestTask2::execute(){

    overwrite_context("t2_s1","skill","run_time",0);
    overwrite_context("t2_s2","skill","run_time",0);

    execute_skill<TestSkill1,SkillParametersTestSkill1>("t2_s1");
    execute_subtask("TestTask1","t2_t1");
    if(get_subtask_result("t2_t1").success){
        return;
    }
    execute_skill<TestSkill1,SkillParametersTestSkill1>("t2_s2");
}
void TestTask2::write_custom_results(nlohmann::json &custom_results){
    custom_results["t2_s1"]=get_result().skill_results["t2_s1"].results;
    custom_results["t2_s2"]=get_result().skill_results["t2_s1"].results;
    custom_results["t2_t1"]=get_subtask_result("t2_t1").custom_results;

    msrm_utils::write_json_array<double,2,1>(custom_results["d"],m_d);
    custom_results["e"]=m_e;
    custom_results["f"]=m_f;
}
bool TestTask2::read_parameters(const nlohmann::json& params){

    spdlog::debug("Reading parameters for task "+get_id());
    if(!msrm_utils::read_json_param<double,2,1>(params,"d",m_d)){
        m_d.setZero();
    }
    if(!msrm_utils::read_json_param(params,"e",m_e)){
        m_e=false;
    }
    if(!msrm_utils::read_json_param(params,"success",m_success)){
        m_success=false;
    }
    if(!msrm_utils::read_json_param(params,"stop_level",m_stop_level)){
        m_stop_level=0;
    }
    spdlog::debug("########## Task parameters ###########");
    std::stringstream mat_ss;
    mat_ss<<m_d;
    spdlog::debug("d: "+mat_ss.str());
    spdlog::debug("e: "+std::to_string(m_e));
    spdlog::debug("success: "+std::to_string(m_success));
    spdlog::debug("stop_level: "+std::to_string(m_stop_level));
    spdlog::debug("########## End ###########");

    return true;
}

void TestTask2::recover_task(){
    spdlog::debug("RECOVERY OF TEST TASK 2");
}

void TestTask2::get_default_context(nlohmann::json &context){
    context["parameters"] = nlohmann::json();
    context["parameters"]["d"]={0,0};
    context["parameters"]["e"]=0;
    context["parameters"]["f"]=false;
    context["parameters"]["stop_level"]=0;
    context["parameters"]["success"]=false;

    context["skills"]=nlohmann::json();
    context["skills"]["t2_s1"]=nlohmann::json();
    context["skills"]["t2_s1"]["control"]={{"control_mode",0}};
    context["skills"]["t2_s1"]["skill"]={{"objects",{{"object","TestObject1"}}}};
    context["skills"]["t2_s1"]["type"]="TestSkill1";
    context["skills"]["t2_s2"]=nlohmann::json();
    context["skills"]["t2_s2"]["control"]={{"control_mode",0}};
    context["skills"]["t2_s2"]["skill"]={{"objects",{{"object","TestObject1"}}}};
    context["skills"]["t2_s2"]["type"]="TestSkill1";
}


}
