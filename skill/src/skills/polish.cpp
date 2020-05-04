#include "skills/polish.hpp"

namespace mios {

polish::polish():Skill("polish"){

}

bool polish::read_skill_parameters(const nlohmann::json &p){
    std::shared_ptr<ConfigSkill_polish> c = std::static_pointer_cast<ConfigSkill_polish>(this->_config);
    msrm_utils::read_json_param(p,"a_x",c->a_x);
    msrm_utils::read_json_param(p,"a_y",c->a_y);
    msrm_utils::read_json_param(p,"f_x",c->f_x);
    msrm_utils::read_json_param(p,"f_y",c->f_y);
    msrm_utils::read_json_param(p,"F_d",c->F_d);
    msrm_utils::read_json_param(p,"t_max",c->t_max);
    return true;
}

void polish::create_config(){
    this->_config=std::make_shared<ConfigSkill_polish>();
}

void polish::build_primitives(const Percept &p){

    this->insert_mp<mp_basic>("polish",p);
    this->set_init_mp("polish");

    std::shared_ptr<ConfigSkill_polish> c = std::static_pointer_cast<ConfigSkill_polish>(this->_config);
    std::shared_ptr<ConfigMP_mp_basic> c_wiggle = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("polish")->get_config());

    c_wiggle->dX_fourier_a_a<<c->a_x,c->a_y,0,0,0,0.5;
    c_wiggle->dX_fourier_a_f<<c->f_x,c->f_y,0,0,0,0.5;
    c_wiggle->dX_fourier_a_phi<<1.78,1.78,0,0,0,1.78;

    std::shared_ptr<AttractorBasic> attr_polish=std::static_pointer_cast<AttractorBasic>(this->get_mp("polish")->get_attractor());
    attr_polish->attr_fc<<0,0,c->F_d,0,0,0;
}

Eigen::Matrix<double,3,3> polish::get_O_R_TF(const Percept &p){
    return this->get_object_pose("surface").block<3,3>(0,0);
}

std::tuple<bool,std::string> polish::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

bool polish::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_polish> c = std::static_pointer_cast<ConfigSkill_polish>(this->_config);
    return p.time-this->get_t_init()>c->t_max;
}

bool polish::check_local_ex_conditions(const Percept &p){
    return true;
}

void polish::evaluate(){
    this->_eval.cost_err=0;
    this->_eval.cost_suc=0;
}

void polish::auxiliaries(const Percept &p){
    if(p.rho(2)<0.3){
        this->set_pause(true);
    }else{
        this->set_pause(false);
    }
}

}
