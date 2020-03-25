#include "skills/hold_pose.hpp"

namespace mios {

hold_pose::hold_pose():Skill("hold_pose"){

}

hold_pose::~hold_pose(){

}

bool hold_pose::read_skill_parameters(const nlohmann::json &p){

    std::shared_ptr<ConfigSkill_hold_pose> c = this->get_config<ConfigSkill_hold_pose>();
    if(!cpp_utils::read_json_param(p,"t_max",c->t_max)){
        cpp_utils::print_error("Missing parameter: t_max");
    }
    return true;
}

void hold_pose::create_config(){
    this->_config=std::make_shared<ConfigSkill_hold_pose>();
}

void hold_pose::build_primitives(const Percept &p){
    this->insert_mp<mp_basic>("hold_pose",p);
    this->set_init_mp("hold_pose");
}

std::tuple<bool,std::string> hold_pose::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

//Eigen::Matrix<double,3,3> hold_pose::get_O_R_TF(const Percept &p){
//    return p.O_T_EE.block<3,3>(0,0);
//}

bool hold_pose::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_hold_pose> c = this->get_config<ConfigSkill_hold_pose>();
    return p.time-this->get_t_init()>c->t_max;
}

bool hold_pose::check_local_ex_conditions(const Percept &p){
    return true;
}

void hold_pose::evaluate(){
    this->_eval.cost_err=this->_eval.p_1.time-this->_eval.p_0.time;
    this->_eval.cost_suc=0;
}

}
