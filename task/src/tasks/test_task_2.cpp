#include "tasks/test_task_2.hpp"

#include "tasks/test_task_1.hpp"
namespace mios{
test_task_2::test_task_2():Task("test_task_2"){
}
test_task_2::~test_task_2(){
}
void test_task_2::initialize_task(){
    this->create_skill<test_skill_1>("t2_s1");
    this->create_skill<test_skill_1>("t2_s2");
    this->create_subtask<test_task_1>("t2_t1");
}
void test_task_2::execute_task(){

    std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t2_s1")->get_config())->run_time=0;
    std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t2_s2")->get_config())->run_time=0;

    this->execute_skill("t2_s1");
    this->execute_subtask("t2_t1");
    if(this->get_subtask("t2_t1")->get_eval().success){
        return;
    }
    this->execute_skill("t2_s2");
}
const EvalTask& test_task_2::evaluate_task(){
    this->_eval_task.success=this->get_subtask("t2_t1")->get_eval().success;
    this->_eval_task.results["t2_s1"]=this->get_skill("t2_s1")->get_eval().results;
    this->_eval_task.results["t2_s2"]=this->get_skill("t2_s2")->get_eval().results;
    this->_eval_task.results["t2_t1"]=this->get_subtask("t2_t1")->get_eval().results;

    cpp_utils::write_json_array<double,2,1>(this->_eval_task.results["d"],d);
    this->_eval_task.results["e"]=e;
    this->_eval_task.results["f"]=f;
    return this->_eval_task;
}
bool test_task_2::read_parameters(const nlohmann::json& params){

    cpp_utils::print_debug("Reading parameters for task "+this->get_id());
    if(!cpp_utils::read_json_param<double,2,1>(params,"d",this->d)){
        this->d.setZero();
    }
    if(!cpp_utils::read_json_param(params,"e",this->e)){
        this->e=false;
    }
    if(!cpp_utils::read_json_param(params,"success",this->success)){
        this->success=false;
    }
    if(!cpp_utils::read_json_param(params,"stop_level",this->stop_level)){
        this->stop_level=0;
    }
    cpp_utils::print_debug("########## Task parameters ###########");
    std::cout<<"d: "<<this->d<<std::endl;
    cpp_utils::print_debug("e: "+std::to_string(this->e));
    cpp_utils::print_debug("success: "+std::to_string(this->success));
    cpp_utils::print_debug("stop_level: "+std::to_string(this->stop_level));
    cpp_utils::print_debug("########## End ###########");

    return true;
}
void test_task_2::recover_task(){
    cpp_utils::print_debug("RECOVERY OF TEST TASK 2");
}
}
