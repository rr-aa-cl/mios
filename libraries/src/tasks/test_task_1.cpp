#include "tasks/test_task_1.hpp"
#include "skills/test_skill_1.hpp"
namespace mios{
TestTask1::TestTask1(Core* core):Task("TestTask1",core),m_result_code(-1),recovered(false){
}
void TestTask1::initialize_context(){
    reserve_skill("t1_s1");
    reserve_skill("t1_s2");
}
void TestTask1::execute(){

    if(m_skill_test==0){
        overwrite_context("t1_s1","skill","success",m_success);
        overwrite_context("t1_s1","skill","exception",m_exception);
        overwrite_context("t1_s1","skill","run_time",3);

        if(m_exception=="task"){
            m_result_code=9;
            throw TaskException("This is a task exception that has been thrown for test purposes");
        }
        execute_skill<TestSkill1,SkillParametersTestSkill1>("t1_s1");
    }

    if(m_skill_test==1){
        overwrite_context("t1_s1","skill","run_time",0);
        overwrite_context("t1_s1","skill","object",{"test_object_1"});


        for(unsigned i=0;i<3;i++){
            overwrite_context("t1_s1","user","dX_max",{i*0.1,i*0.5});
            execute_skill<TestSkill1,SkillParametersTestSkill1>("t1_s2");
        }
    }
    if(m_skill_test==2){
        overwrite_context("t1_s2","skill","run_time",3);
        overwrite_context("t1_s2","skill","parallels_frequency",100);
        execute_skill<TestSkill1,SkillParametersTestSkill1>("t1_s2");
    }
    if(m_skill_test==3){
        overwrite_context("t1_s2","skill","run_time",0);
        overwrite_context("t1_s1","skill","object",{"test_object_2"});
        for(unsigned i=0;i<3;i++){
            execute_skill<TestSkill1,SkillParametersTestSkill1>("t1_s2");
        }
    }
    if(m_skill_test==4){
        overwrite_context("t1_s1","skill","success",true);
        overwrite_context("t1_s1","skill","mp_sequence",m_mp_sequence);
        for(unsigned i=0;i<3;i++){
            execute_skill<TestSkill1,SkillParametersTestSkill1>("t1_s1");
        }
    }
    m_result_code=-1;

}
void TestTask1::evaluate(){
    nlohmann::json custom_results;
    custom_results["t1_s1"]=get_result().skill_results["t1_s1"].results;
    custom_results["t1_s2"]=get_result().skill_results["t1_s2"].results;
    custom_results["result_code"]=m_result_code;
    custom_results["queue_number"]=m_queue_number;
    custom_results["recovered"]=recovered;
    msrm_utils::write_json_array<double,3,1>(custom_results["a"],m_a);
    custom_results["b"]=m_b;
    write_result(get_result().skill_results["t1_s1"].success,get_result().skill_results["t1_s1"].cost_suc,get_result().skill_results["t1_s1"].cost_err,custom_results);
}
bool TestTask1::read_parameters(const nlohmann::json& params){
    spdlog::debug("Reading parameters for task "+this->get_id());

    if(!msrm_utils::read_json_param(params,"b",m_b)){
        m_b=0;
    }
    if(!msrm_utils::read_json_param<double,3,1>(params,"a",m_a)){
        m_a.setZero();
    }
    if(!msrm_utils::read_json_param(params,"success",m_success)){
        m_success=false;
    }
    if(!msrm_utils::read_json_param(params,"exception",m_exception)){
        m_exception="none";
    }
    if(!msrm_utils::read_json_param(params,"skill_test",m_skill_test)){
        m_skill_test=0;
    }
    if(!msrm_utils::read_json_param(params,"queue_number",m_queue_number)){
        m_queue_number=0;
    }
    if(!msrm_utils::read_json_param(params,"mp_sequence",m_mp_sequence)){
        m_mp_sequence.resize(0);
    }
    spdlog::debug("########## Task parameters ###########");
    std::cout<<"a: "<<m_a<<std::endl;
    spdlog::debug("b: "+std::to_string(m_b));
    spdlog::debug("success: "+std::to_string(m_success));
    spdlog::debug("exception: "+m_exception);
    spdlog::debug("########## End ###########");

    return true;
}

void TestTask1::recover_task(){
    recovered=true;
    spdlog::debug("RECOVERY OF TEST TASK 1");
}
}
