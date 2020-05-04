#include "skills/push.hpp"

namespace mios {

push::push():Skill("push"){

}

bool push::read_skill_parameters(const nlohmann::json &p){
    std::shared_ptr<ConfigSkill_push> c = std::static_pointer_cast<ConfigSkill_push>(this->_config);
    if(!msrm_utils::read_json_param(p,"F_d",c->F_d)){
        msrm_utils::print_error("Missing parameter: F_d");
    }
    if(!msrm_utils::read_json_param(p,"t_max",c->t_max)){
        msrm_utils::print_error("Missing parameter: t_max");
    }
    return true;
}

void push::create_config(){
    this->_config=std::make_shared<ConfigSkill_push>();
}

void push::build_primitives(const Percept &p){
    this->insert_mp<mp_basic>("push",p);
    this->set_init_mp("push");

    std::shared_ptr<ConfigSkill_push> c = std::static_pointer_cast<ConfigSkill_push>(this->_config);

    std::shared_ptr<AttractorBasic> attr_push=std::static_pointer_cast<AttractorBasic>(this->get_mp("push")->get_attractor());
    attr_push->attr_fc<<0,0,c->F_d,0,0,0;
}

std::tuple<bool,std::string> push::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

Eigen::Matrix<double,3,3> push::get_O_R_TF(const Percept &p){
    return p.O_T_EE.block<3,3>(0,0);
}

bool push::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_push> c = std::static_pointer_cast<ConfigSkill_push>(this->_config);
    return p.time-this->get_t_init()>c->t_max;
}

bool push::check_local_ex_conditions(const Percept &p){
    return true;
}

void push::evaluate(){
    this->_eval.cost_err=this->_eval.p_1.time-this->_eval.p_0.time;
    this->_eval.cost_suc=0;
}

}
