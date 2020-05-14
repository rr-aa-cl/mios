#include "tasks/test_task_3.hpp"
#include "tasks/test_task_1.hpp"
#include "tasks/test_task_2.hpp"
#include "skills/test_skill_1.hpp"
namespace mios{
TestTask3::TestTask3(Core *core):Task("TestTask3",core){
}
void TestTask3::initialize_task(){
    this->create_skill<test_skill_1>("t3_s1",m_kb,std::make_shared<SkillParameters_test_skill_1>());
    this->create_skill<test_skill_1>("t3_s2",m_kb,std::make_shared<SkillParameters_test_skill_1>());
    this->create_skill<test_skill_1>("t3_s3",m_kb,std::make_shared<SkillParameters_test_skill_1>());
    this->create_subtask<TestTask1>("t3_t1");
    this->create_subtask<TestTask2>("t3_t2");
}
void TestTask3::execute_task(){

    std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t3_s1")->get_config())->run_time=0;
    std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t3_s2")->get_config())->run_time=0;
    std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t3_s3")->get_config())->run_time=0;

    this->execute_skill("t3_s1");
    this->execute_subtask("t3_t1");
    this->execute_skill("t3_s2");
    this->execute_subtask("t3_t2");
    this->execute_skill("t3_s2");
}
const EvalTask& TestTask3::evaluate_task(){
    m_eval_task.results["t3_s1"]=this->get_skill("t3_s1")->get_eval().results;
    m_eval_task.results["t3_s2"]=this->get_skill("t3_s2")->get_eval().results;
    m_eval_task.results["t3_s3"]=this->get_skill("t3_s3")->get_eval().results;
    m_eval_task.results["t3_t1"]=this->get_subtask("t3_t1")->get_eval().results;
    m_eval_task.results["t3_t2"]=this->get_subtask("t3_t2")->get_eval().results;
    msrm_utils::write_json_array<double,4,1>(m_eval_task.results["g"],g);
    m_eval_task.results["h"]=h;
    m_eval_task.results["i"]=i;
    return m_eval_task;
}
bool TestTask3::read_parameters(const nlohmann::json& params){
    msrm_utils::print_debug("Reading parameters for task "+this->get_id());
    if(!msrm_utils::read_json_param<double,4,1>(params,"g",this->g)){
        this->g.setZero();
    }
    if(!msrm_utils::read_json_param(params,"h",this->h)){
        this->h=false;
    }
    if(!msrm_utils::read_json_param(params,"i",this->i)){
        this->i=0;
    }
    if(!msrm_utils::read_json_param(params,"j",this->j)){
        this->j="none";
    }
    if(!msrm_utils::read_json_param(params,"success",this->success)){
        this->success=false;
    }
    if(!msrm_utils::read_json_param(params,"stop_level",this->stop_level)){
        this->stop_level=0;
    }
    msrm_utils::print_debug("########## Task parameters ###########");
    std::cout<<"g: "<<this->g<<std::endl;
    msrm_utils::print_debug("h: "+std::to_string(this->h));
    msrm_utils::print_debug("i: "+std::to_string(this->i));
    msrm_utils::print_debug("j: "+this->j);
    msrm_utils::print_debug("success: "+std::to_string(this->success));
    msrm_utils::print_debug("stop_level: "+std::to_string(this->stop_level));
    msrm_utils::print_debug("########## End ###########");
    return true;
}

void TestTask3::recover_task(){
    msrm_utils::print_debug("RECOVERY OF TEST TASK 3");
}

}
