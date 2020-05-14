#include "tasks/test_task_1.hpp"
#include "skills/test_skill_1.hpp"
namespace mios{
TestTask1::TestTask1(Core* core):Task("TestTask1",core){
}
void TestTask1::initialize_task(){
    this->create_skill<test_skill_1>("t1_s1",m_kb,std::make_shared<SkillParameters_test_skill_1>());
    this->create_skill<test_skill_1>("t1_s2",m_kb,std::make_shared<SkillParameters_test_skill_1>());
}
void TestTask1::execute_task(){

    if(this->skill_test==0){

        std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t1_s1")->get_config())->success=this->success;
        std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t1_s1")->get_config())->exception=this->exception;
        if(this->exception=="task"){
            throw TaskException("This is a task exception that has been thrown for test purposes");
        }
        this->execute_skill("t1_s1");
    }

    if(this->skill_test==1){
        std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t1_s2")->get_config())->run_time=0;
        this->get_skill("t1_s2")->set_object("object","test_object_1");
        for(unsigned i=0;i<3;i++){
            std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t1_s2")->get_config())->user.dX_max<<i*0.1,i*0.5;
            this->execute_skill("t1_s2");
        }
    }
    if(this->skill_test==2){
        std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t1_s2")->get_config())->run_time=3;
        std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t1_s2")->get_config())->parallels_frequency=100;
        this->execute_skill("t1_s2");
    }
    if(this->skill_test==3){
        std::static_pointer_cast<SkillParameters_test_skill_1>(this->get_skill("t1_s2")->get_config())->run_time=0;
        this->get_skill("t1_s2")->set_object("object","test_object_2");
        for(unsigned i=0;i<3;i++){
            this->execute_skill("t1_s2");
        }
    }

}
const EvalTask& TestTask1::evaluate_task(){
    m_eval_task.success=this->get_skill("t1_s1")->get_eval().success;
    m_eval_task.cost_suc=this->get_skill("t1_s1")->get_eval().cost_suc;
    m_eval_task.cost_err=this->get_skill("t1_s1")->get_eval().cost_err;

    m_eval_task.results["t1_s1"]=this->get_skill("t1_s1")->get_eval().results;
    m_eval_task.results["t1_s2"]=this->get_skill("t1_s2")->get_eval().results;
    msrm_utils::write_json_array<double,3,1>(m_eval_task.results["a"],a);
    m_eval_task.results["b"]=b;
    return m_eval_task;
}
bool TestTask1::read_parameters(const nlohmann::json& params){
    msrm_utils::print_debug("Reading parameters for task "+this->get_id());

    if(!msrm_utils::read_json_param(params,"b",this->b)){
        //        msrm_utils::print_error("Could not load parameter: b [bool]");
        this->b=0;
    }
    if(!msrm_utils::read_json_param<double,3,1>(params,"a",this->a)){
        //        msrm_utils::print_error("Could not load parameter: a [double,3,1]");
        this->a.setZero();
    }
    if(!msrm_utils::read_json_param(params,"success",this->success)){
        this->success=false;
    }
    if(!msrm_utils::read_json_param(params,"exception",this->exception)){
        this->exception="none";
    }
    if(!msrm_utils::read_json_param(params,"skill_test",this->skill_test)){
        this->skill_test=0;
    }
    msrm_utils::print_debug("########## Task parameters ###########");
    std::cout<<"a: "<<this->a<<std::endl;
    msrm_utils::print_debug("b: "+std::to_string(this->b));
    msrm_utils::print_debug("success: "+std::to_string(this->success));
    msrm_utils::print_debug("exception: "+this->exception);
    msrm_utils::print_debug("########## End ###########");

    return true;
}

void TestTask1::recover_task(){
    msrm_utils::print_debug("RECOVERY OF TEST TASK 1");
}
}
