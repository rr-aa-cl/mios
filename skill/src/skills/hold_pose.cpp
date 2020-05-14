#include "skills/hold_pose.hpp"

namespace mios {

hold_pose::hold_pose(KnowledgeBase *kb, std::shared_ptr<SkillParameters> config):Skill("hold_pose",kb,config){

}

bool hold_pose::read_skill_parameters(const nlohmann::json &p){

    std::shared_ptr<SkillParameters_hold_pose> c = this->get_config<SkillParameters_hold_pose>();
    if(!msrm_utils::read_json_param(p,"t_max",c->t_max)){
        msrm_utils::print_error("Missing parameter: t_max");
    }
    return true;
}

void hold_pose::create_config(){
    m_config=std::make_shared<SkillParameters_hold_pose>();
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
    std::shared_ptr<SkillParameters_hold_pose> c = this->get_config<SkillParameters_hold_pose>();
    return p.time-this->get_t_init()>c->t_max;
}

bool hold_pose::check_local_ex_conditions(const Percept &p){
    return true;
}

void hold_pose::evaluate(){
    m_eval.cost_err=m_eval.p_1.time-m_eval.p_0.time;
    m_eval.cost_suc=0;
}

}
