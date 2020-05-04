#include "skills/move_to_contact.hpp"

namespace mios {

move_to_contact::move_to_contact():Skill("move_to_contact"){

}

bool move_to_contact::read_skill_parameters(const nlohmann::json &p){

    std::shared_ptr<ConfigSkill_move_to_contact> c = std::static_pointer_cast<ConfigSkill_move_to_contact>(this->_config);
    msrm_utils::read_json_param<double,1,1>(p,"speed",c->speed);
    return true;
}

void move_to_contact::create_config(){
    this->_config=std::make_shared<ConfigSkill_move_to_contact>();
}

void move_to_contact::build_primitives(const Percept &p){
    this->insert_mp<mp_basic>("contact",p);
    this->set_init_mp("contact");

    std::shared_ptr<ConfigMP_mp_basic> c_contact = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("contact")->get_config());

    std::shared_ptr<ConfigSkill_move_to_contact> c = std::static_pointer_cast<ConfigSkill_move_to_contact>(this->_config);

    std::shared_ptr<AttractorBasic> attr_move_to_pose=std::static_pointer_cast<AttractorBasic>(this->get_mp("contact")->get_attractor());
    attr_move_to_pose->attr_vel<<0,0,c->user.dX_max(0)*c->speed(0),0,0,0;
}

std::tuple<bool,std::string> move_to_contact::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

Eigen::Matrix<double,3,3> move_to_contact::get_O_R_TF(const Percept &p){
    return this->get_object("surface").O_T_o.block<3,3>(0,0);
}


bool move_to_contact::check_local_suc_conditions(const Percept &p){
    return p.TF_F_ext(2)>this->_config->user.F_contact(2);
}

bool move_to_contact::check_local_ex_conditions(const Percept &p){
    return true;
}

void move_to_contact::evaluate(){
    this->_eval.cost_err=this->_eval.p_1.time-this->_eval.p_0.time;
    this->_eval.cost_suc=0;
}

}
