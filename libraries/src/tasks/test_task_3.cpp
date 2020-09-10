#include "tasks/test_task_3.hpp"
#include "tasks/test_task_1.hpp"
#include "tasks/test_task_2.hpp"
#include "skills/test_skill_1.hpp"
namespace mios{
TestTask3::TestTask3(Core *core):Task("TestTask3",core),recovered(false){
}
void TestTask3::initialize_context(){
    reserve_skill("t3_s1");
    reserve_skill("t3_s2");
    reserve_skill("t3_s3");
    reserve_subtask("t3_t1");
    reserve_subtask("t3_t2");
}
void TestTask3::execute(){

    overwrite_context("t3_s1","skill","run_time",0);
    overwrite_context("t3_s2","skill","run_time",0);
    overwrite_context("t3_s3","skill","run_time",0);

    execute_skill<TestSkill1,SkillParametersTestSkill1>("t3_s1");
    execute_subtask("TestTask2","t3_t1");
    execute_skill<TestSkill1,SkillParametersTestSkill1>("t3_s2");
    execute_subtask("TestTask1","t3_t2");

}
void TestTask3::write_custom_results(nlohmann::json &custom_results){
    custom_results["t3_s1"]=get_result().skill_results["t3_s1"].results;
    custom_results["t3_s2"]=get_result().skill_results["t3_s2"].results;
    custom_results["t3_s3"]=get_result().skill_results["t3_s3"].results;
    custom_results["t3_t1"]=get_subtask_result("t3_t1").custom_results;
    custom_results["t3_t2"]=get_subtask_result("t3_t2").custom_results;
    msrm_utils::write_json_array<double,4,1>(custom_results["g"],m_g);
    custom_results["h"]=m_h;
    custom_results["i"]=m_i;
    custom_results["recovered"]=recovered;
}
bool TestTask3::read_parameters(const nlohmann::json& params){
    spdlog::debug("Reading parameters for task "+this->get_id());
    if(!msrm_utils::read_json_param<double,4,1>(params,"g",m_g)){
        m_g.setZero();
    }
    if(!msrm_utils::read_json_param(params,"h",m_h)){
        m_h=false;
    }
    if(!msrm_utils::read_json_param(params,"i",m_i)){
        m_i=0;
    }
    if(!msrm_utils::read_json_param(params,"j",m_j)){
        m_j="none";
    }
    if(!msrm_utils::read_json_param(params,"success",m_success)){
        m_success=false;
    }
    if(!msrm_utils::read_json_param(params,"stop_level",m_stop_level)){
        m_stop_level=0;
    }
    spdlog::debug("########## Task parameters ###########");
    std::stringstream ss_g;
    ss_g<<m_g;
    spdlog::debug("g: " + ss_g.str());
    spdlog::debug("h: "+std::to_string(m_h));
    spdlog::debug("i: "+std::to_string(m_i));
    spdlog::debug("j: "+m_j);
    spdlog::debug("success: "+std::to_string(m_success));
    spdlog::debug("stop_level: "+std::to_string(m_stop_level));
    spdlog::debug("########## End ###########");
    return true;
}

void TestTask3::recover_task(){
    recovered=true;
    spdlog::debug("RECOVERY OF TEST TASK 3");
}

void TestTask3::get_default_context(nlohmann::json &context){
    context["parameters"] = nlohmann::json();
    context["parameters"]["g"]={0,0,0,0};
    context["parameters"]["h"]=false;
    context["parameters"]["i"]=0;
    context["parameters"]["j"]="";
    context["parameters"]["stop_level"]=0;
    context["parameters"]["success"]=false;

    context["skills"]=nlohmann::json();
    context["skills"]["t3_s1"]=nlohmann::json();
    context["skills"]["t3_s1"]["control"]={{"control_mode",0}};
    context["skills"]["t3_s1"]["skill"]={{"objects",{{"object","TestObject1"}}}};
    context["skills"]["t3_s1"]["type"]="TestSkill1";
    context["skills"]["t3_s2"]=nlohmann::json();
    context["skills"]["t3_s2"]["control"]={{"control_mode",0}};
    context["skills"]["t3_s2"]["skill"]={{"objects",{{"object","TestObject1"}}}};
    context["skills"]["t3_s2"]["type"]="TestSkill1";
    context["skills"]["t3_s3"]=nlohmann::json();
    context["skills"]["t3_s3"]["control"]={{"control_mode",0}};
    context["skills"]["t3_s3"]["skill"]={{"objects",{{"object","TestObject1"}}}};
    context["skills"]["t3_s3"]["type"]="TestSkill1";
}

}
