#include "tasks/test_task_2.hpp"
#include "tasks/test_task_1.hpp"
#include "skills/test_skill_1.hpp"
namespace mios{
TestTask2::TestTask2(Core* core):Task("TestTask2",core){
}
void TestTask2::initialize_task(){
    this->create_skill<test_skill_1>("t2_s1",m_kb,std::make_shared<SkillParameters_test_skill_1>());
    this->create_skill<test_skill_1>("t2_s2",m_kb,std::make_shared<SkillParameters_test_skill_1>());
    this->create_subtask<TestTask1>("t2_t1");
}
void TestTask2::execute_task(){

    std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t2_s1")->get_config())->run_time=0;
    std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t2_s2")->get_config())->run_time=0;

    this->execute_skill("t2_s1");
    this->execute_subtask("t2_t1");
    if(this->get_subtask("t2_t1")->get_eval().success){
        return;
    }
    this->execute_skill("t2_s2");
}
const EvalTask& TestTask2::evaluate_task(){
    m_eval_task.success=this->get_subtask("t2_t1")->get_eval().success;
    m_eval_task.results["t2_s1"]=this->get_skill("t2_s1")->get_eval().results;
    m_eval_task.results["t2_s2"]=this->get_skill("t2_s2")->get_eval().results;
    m_eval_task.results["t2_t1"]=this->get_subtask("t2_t1")->get_eval().results;

    msrm_utils::write_json_array<double,2,1>(m_eval_task.results["d"],d);
    m_eval_task.results["e"]=e;
    m_eval_task.results["f"]=f;
    return m_eval_task;
}
bool TestTask2::read_parameters(const nlohmann::json& params){

    msrm_utils::print_debug("Reading parameters for task "+this->get_id());
    if(!msrm_utils::read_json_param<double,2,1>(params,"d",this->d)){
        this->d.setZero();
    }
    if(!msrm_utils::read_json_param(params,"e",this->e)){
        this->e=false;
    }
    if(!msrm_utils::read_json_param(params,"success",this->success)){
        this->success=false;
    }
    if(!msrm_utils::read_json_param(params,"stop_level",this->stop_level)){
        this->stop_level=0;
    }
    msrm_utils::print_debug("########## Task parameters ###########");
    std::cout<<"d: "<<this->d<<std::endl;
    msrm_utils::print_debug("e: "+std::to_string(this->e));
    msrm_utils::print_debug("success: "+std::to_string(this->success));
    msrm_utils::print_debug("stop_level: "+std::to_string(this->stop_level));
    msrm_utils::print_debug("########## End ###########");

    return true;
}
void TestTask2::recover_task(){
    msrm_utils::print_debug("RECOVERY OF TEST TASK 2");
}
}
