#include "tasks/test_task_1.hpp"
namespace mios{
test_task_1::test_task_1():Task("test_task_1"){
}
test_task_1::~test_task_1(){
}
void test_task_1::initialize_task(){
    this->create_skill<test_skill_1>("t1_s1");
    this->create_skill<test_skill_1>("t1_s2");
}
void test_task_1::execute_task(){

    if(this->skill_test==0){

        std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t1_s1")->get_config())->success=this->success;
        std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t1_s1")->get_config())->exception=this->exception;
        if(this->exception=="task"){
            throw TaskException("This is a task exception that has been thrown for test purposes");
        }
        this->execute_skill("t1_s1");
    }

    if(this->skill_test==1){
        std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t1_s2")->get_config())->run_time=0;
        this->get_skill("t1_s2")->set_object("object","test_object_1");
        for(unsigned i=0;i<3;i++){
            std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t1_s2")->get_config())->user.dX_max<<i*0.1,i*0.5;
            this->execute_skill("t1_s2");
        }
    }
    if(this->skill_test==2){
        std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t1_s2")->get_config())->run_time=3;
        std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t1_s2")->get_config())->parallels_frequency=100;
        this->execute_skill("t1_s2");
    }
    if(this->skill_test==3){
        std::static_pointer_cast<ConfigSkill_test_skill_1>(this->get_skill("t1_s2")->get_config())->run_time=0;
        this->get_skill("t1_s2")->set_object("object","test_object_2");
        for(unsigned i=0;i<3;i++){
            this->execute_skill("t1_s2");
        }
    }

}
const EvalTask& test_task_1::evaluate_task(){
    this->_eval_task.success=this->get_skill("t1_s1")->get_eval().success;
    this->_eval_task.cost_suc=this->get_skill("t1_s1")->get_eval().cost_suc;
    this->_eval_task.cost_err=this->get_skill("t1_s1")->get_eval().cost_err;

    this->_eval_task.results["t1_s1"]=this->get_skill("t1_s1")->get_eval().results;
    this->_eval_task.results["t1_s2"]=this->get_skill("t1_s2")->get_eval().results;
    cpp_utils::write_json_array<double,3,1>(this->_eval_task.results["a"],a);
    this->_eval_task.results["b"]=b;
    return this->_eval_task;
}
bool test_task_1::read_parameters(const nlohmann::json& params){
    cpp_utils::print_debug("Reading parameters for task "+this->get_id());

    if(!cpp_utils::read_json_param(params,"b",this->b)){
        //        cpp_utils::print_error("Could not load parameter: b [bool]");
        this->b=0;
    }
    if(!cpp_utils::read_json_param<double,3,1>(params,"a",this->a)){
        //        cpp_utils::print_error("Could not load parameter: a [double,3,1]");
        this->a.setZero();
    }
    if(!cpp_utils::read_json_param(params,"success",this->success)){
        this->success=false;
    }
    if(!cpp_utils::read_json_param(params,"exception",this->exception)){
        this->exception="none";
    }
    if(!cpp_utils::read_json_param(params,"skill_test",this->skill_test)){
        this->skill_test=0;
    }
    cpp_utils::print_debug("########## Task parameters ###########");
    std::cout<<"a: "<<this->a<<std::endl;
    cpp_utils::print_debug("b: "+std::to_string(this->b));
    cpp_utils::print_debug("success: "+std::to_string(this->success));
    cpp_utils::print_debug("exception: "+this->exception);
    cpp_utils::print_debug("########## End ###########");

    return true;
}

void test_task_1::recover_task(){
    cpp_utils::print_debug("RECOVERY OF TEST TASK 1");
}
}
