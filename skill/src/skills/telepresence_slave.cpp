#include "skills/telepresence_slave.hpp"

namespace mios {

telepresence_slave::telepresence_slave():Skill("telepresence_slave"){

}

bool telepresence_slave::read_skill_parameters(const nlohmann::json &p){

    std::shared_ptr<ConfigSkill_telepresence_slave> c = std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->_config);

    if(!cpp_utils::read_json_param(p,"ip_dst",c->ip_dst)){
        cpp_utils::print_error("Missing parameter: ip_dst");
        return false;
    }
    if(!cpp_utils::read_json_param(p,"port_dst",c->port_dst)){
        cpp_utils::print_error("Missing parameter: port_dst");
        return false;
    }
    if(!cpp_utils::read_json_param(p,"port_recv",c->port_recv)){
        cpp_utils::print_error("Missing parameter: port_recv");
        return false;
    }
    if(!cpp_utils::read_json_param(p,"repeater",c->repeater)){
        c->repeater=false;
    }
    if(!cpp_utils::read_json_param(p,"bilateral",c->bilateral)){
        c->bilateral=true;
    }
    if(!cpp_utils::read_json_param<double,3,3>(p,"EE_T_J_t",c->EE_T_J_t)){
        c->EE_T_J_t=Eigen::Matrix<double,3,3>::Identity();
    }
    if(!cpp_utils::is_orthonormal(c->EE_T_J_t)){
        cpp_utils::print_error("Matrix EE_T_J_t is not orthonormal.");
        return false;
    }
    if(!cpp_utils::read_json_param<double,3,3>(p,"EE_T_J_r",c->EE_T_J_r)){
        c->EE_T_J_r=Eigen::Matrix<double,3,3>::Identity();
    }
    if(!cpp_utils::is_orthonormal(c->EE_T_J_r)){
        cpp_utils::print_error("Matrix EE_T_J_r is not orthonormal.");
        return false;
    }
    std::string mode;
    if(!cpp_utils::read_json_param(p,"mode",mode)){
        cpp_utils::print_error("Missing parameter: mode");
        return false;
    }
    if(mode=="joystick"){
        c->mode=TelepresenceMode::Joystick;
    }
    return true;
}

void telepresence_slave::create_config(){
    this->_config=std::make_shared<ConfigSkill_telepresence_slave>();
}

void telepresence_slave::build_primitives(const Percept &p){
    this->insert_mp<mp_telepresence>("telepresence",p);
    this->set_init_mp("telepresence");

    std::shared_ptr<ConfigMP_mp_telepresence> c_network = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->get_mp("telepresence")->get_config());
    std::shared_ptr<ConfigSkill_telepresence_slave> c = std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->_config);

    c_network->ip_dst=c->ip_dst;
    c_network->port_dst=c->port_dst;
    c_network->port_recv=c->port_recv;
    c_network->repeater=c->repeater;
    c_network->master=false;
    c_network->bilateral=c->bilateral;
    c_network->EE_T_J_t=c->EE_T_J_t;
    c_network->EE_T_J_r=c->EE_T_J_r;
    c_network->mode=c->mode;
}

std::tuple<bool,std::string> telepresence_slave::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

bool telepresence_slave::check_local_suc_conditions(const Percept &p){
    return false;
}

bool telepresence_slave::check_local_ex_conditions(const Percept &p){
    return true;
}

bool telepresence_slave::check_local_err_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_telepresence_slave> c = std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->_config);
//    if(c->joint_mode){
//        for(unsigned i=0;i<7;i++){
//            if(fabs(this->_cmd.q_d(i)-p.q(i))>0.1){
//                std::cout<<"q_d: "<<this->_cmd.q_d<<std::endl;
//                std::cout<<"q: "<<p.q<<std::endl;
//                return true;
//            }
//        }
//    }else{
//        for(unsigned i=0;i<3;i++){
//            if(fabs(this->_cmd.TF_T_EE_d(0,i)-p.O_T_EE(0,i))>c->DX_max(0)){
//                return true;
//            }
//        }
//    }
    return false;
}

void telepresence_slave::evaluate(){
    this->_eval.cost_err=0;
    this->_eval.cost_suc=0;
}

}
