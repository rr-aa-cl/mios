#include "skills/telepresence_master.hpp"

namespace mios {

telepresence_master::telepresence_master():Skill("telepresence_master"){

}

bool telepresence_master::read_skill_parameters(const nlohmann::json &p){

    std::shared_ptr<ConfigSkill_telepresence_master> c = std::static_pointer_cast<ConfigSkill_telepresence_master>(this->_config);

    if(!msrm_utils::read_json_param<unsigned>(p,"port_dst",c->port_dst)){
        msrm_utils::print_error("Missing parameter: port_dst");
        return false;
    }
    if(!msrm_utils::read_json_param<std::string>(p,"ip_dst",c->ip_dst)){
        msrm_utils::print_error("Missing parameter: ip_dst");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"port_recv",c->port_recv)){
        msrm_utils::print_error("Missing parameter: port_recv");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"bilateral",c->bilateral)){
        c->bilateral=true;
    }
    if(!msrm_utils::read_json_param<double,6,1>(p,"K_joystick_on",c->K_joystick_on)){
        c->K_joystick_on.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(p,"K_joystick_off",c->K_joystick_off)){
        c->K_joystick_off.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(p,"joystick_deadband",c->joystick_deadband)){
        c->joystick_deadband.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(p,"joystick_amp",c->joystick_amp)){
        c->joystick_amp.setZero();
    }
    if(!msrm_utils::read_json_param(p,"joystick_force_input",c->joystick_force_input)){
        c->joystick_force_input=false;
    }
    std::string mode;
    if(!msrm_utils::read_json_param(p,"mode",mode)){
        msrm_utils::print_error("Missing parameter: mode");
        return false;
    }
    if(mode=="joystick"){
        c->mode=TelepresenceMode::Joystick;
    }

    return true;
}

void telepresence_master::create_config(){
    this->_config=std::make_shared<ConfigSkill_telepresence_master>();
}

void telepresence_master::build_primitives(const Percept &p){
    this->insert_mp<mp_telepresence>("telepresence",p);
    this->set_init_mp("telepresence");

    std::shared_ptr<ConfigMP_mp_telepresence> c_network = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->get_mp("telepresence")->get_config());
    std::shared_ptr<ConfigSkill_telepresence_master> c = std::static_pointer_cast<ConfigSkill_telepresence_master>(this->_config);

    c_network->ip_dst=c->ip_dst;
    c_network->port_dst=c->port_dst;
    c_network->port_recv=c->port_recv;
    c_network->master=true;
    c_network->bilateral=c->bilateral;
    c_network->K_joystick_off=c->K_joystick_off;
    c_network->K_joystick_on=c->K_joystick_on;
    c_network->mode=c->mode;
    c_network->joystick_deadband=c->joystick_deadband;
    c_network->joystick_amp=c->joystick_amp;
    c_network->joystick_lever=c->frames.F_T_EE.block<3,1>(0,3);
    c_network->joystick_f_ext_amp=c->joystick_f_ext_amp;
    c_network->joystick_force_input=c->joystick_force_input;
}

std::tuple<bool,std::string> telepresence_master::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

bool telepresence_master::check_local_suc_conditions(const Percept &p){
    return false;
}

bool telepresence_master::check_local_ex_conditions(const Percept &p){
    return true;
}

void telepresence_master::evaluate(){
    this->_eval.cost_err=0;
    this->_eval.cost_suc=0;
}

}
