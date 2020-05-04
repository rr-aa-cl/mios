#include "skills/test_skill_1.hpp"

#include <franka/exception.h>

namespace mios{
test_skill_1::test_skill_1():Skill("test_skill_1"){}
test_skill_1::~test_skill_1(){}
bool test_skill_1::read_skill_parameters(const nlohmann::json& p){
    msrm_utils::print_debug("Start of reading skill parameters for skill "+this->get_id());
    std::shared_ptr<ConfigSkill_test_skill_1> c = std::static_pointer_cast<ConfigSkill_test_skill_1>(this->_config);
    if(!msrm_utils::read_json_param(p,"run_time",c->run_time)){
        msrm_utils::print_debug("Could not load parameter: run_time [double]");
        return false;
    }
    std::cout<<p<<std::endl;
    if(!msrm_utils::read_json_param(p,"success",c->success)){
        c->success=false;
    }
    if(!msrm_utils::read_json_param(p,"t_exception",c->t_exception)){
        c->t_exception=0;
    }
    if(!msrm_utils::read_json_param(p,"exception",c->exception)){
        c->exception="none";
    }

    msrm_utils::print_debug("###############################   Skill parameters   ######################################");
    msrm_utils::print_debug("run_time: "+std::to_string(c->run_time));
    msrm_utils::print_debug("success: "+std::to_string(c->success));
    msrm_utils::print_debug("t_exception: "+std::to_string(c->t_exception));
    msrm_utils::print_debug("exception: "+c->exception);
    msrm_utils::print_debug("###########################################################################################");

    return true;
}
void test_skill_1::build_primitives(const Percept& p){
    msrm_utils::print_debug("Begin of build_primitives");
    this->insert_mp<mp_basic>("mp",p);
    this->set_init_mp("mp");

    this->_eval.results["parallels_cnt"]=0;
    msrm_utils::print_debug("End of build_primitives");
}
std::tuple<bool,std::string> test_skill_1::check_edges(const Percept& p){return std::tuple<bool,std::string>(false,"");}

bool test_skill_1::check_local_suc_conditions(const Percept& p){
    std::shared_ptr<ConfigSkill_test_skill_1> c = std::static_pointer_cast<ConfigSkill_test_skill_1>(this->_config);
    if(c->success && p.time-this->_eval.p_0.time>c->run_time){
        msrm_utils::print_debug("Local success condition triggered at "+std::to_string(p.time-this->_eval.p_0.time));
        return true;
    }else{
        return false;
    }
}

bool test_skill_1::check_local_err_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_test_skill_1> c = std::static_pointer_cast<ConfigSkill_test_skill_1>(this->_config);
    if(!c->success && p.time-this->_eval.p_0.time>c->run_time){
        msrm_utils::print_debug("Local error condition triggered at "+std::to_string(p.time-this->_eval.p_0.time));
        return true;
    }else{
        return false;
    }
}

Eigen::Matrix<double,3,3> test_skill_1::get_O_R_TF(const Percept &p){
    msrm_utils::print_debug("O_R_TF");
    Eigen::Matrix<double,3,3> R = this->get_object_pose("object",false).block<3,3>(0,0);
    Object o = this->get_object("object");
    return R;
}

void test_skill_1::auxiliaries(const Percept &p){
    std::shared_ptr<ConfigSkill_test_skill_1> c = std::static_pointer_cast<ConfigSkill_test_skill_1>(this->_config);
    double a=c->t_exception;
    if(p.time-this->_eval.p_0.time>c->t_exception){
        if(c->exception=="control"){
            throw franka::ControlException("This is a control exception that has been thrown for test purposes");
        }
        if(c->exception=="invalid"){
            throw franka::InvalidOperationException("This is an invalid operation exception that has been thrown for test purposes");
        }
        if(c->exception=="network"){
            throw franka::NetworkException("This is a network exception that has been thrown for test purposes");
        }
        if(c->exception=="realtime"){
            throw franka::RealtimeException("This is a realtime exception that has been thrown for test purposes");
        }
        if(c->exception=="skill"){
            throw SkillException("This is a skill exception that has been thrown for test purposes");
        }
    }
}
void test_skill_1::evaluate(){
    msrm_utils::print_debug("Evaluate");
    std::shared_ptr<ConfigSkill_test_skill_1> c = std::static_pointer_cast<ConfigSkill_test_skill_1>(this->_config);
    this->_eval.results["test_parameter_1"]=this->_kb->get_live_parameter("test_parameter_1");
    this->_eval.results["test_parameter_2"]=this->_kb->get_live_parameter("test_parameter_2");
    this->_eval.results["test_parameter_3"]=this->_kb->get_live_parameter("test_parameter_3");

    this->_eval.results["exception"]=c->exception;
    this->_eval.results["run_time"]=c->run_time;
    this->_eval.results["success"]=c->success;
    this->_eval.results["t_exception"]=c->t_exception;
}
void test_skill_1::create_config(){
this->_config=std::make_shared<ConfigSkill_test_skill_1>();
}

void test_skill_1::parallels(){
    double cnt;
    msrm_utils::read_json_param(this->_eval.results,"parallels_cnt",cnt);
    this->_eval.results["parallels_cnt"]=cnt+1;
}
}
