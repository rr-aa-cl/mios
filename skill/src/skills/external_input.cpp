#include "skills/external_input.hpp"
namespace mios{
external_input::external_input():Skill("external_input"){}
bool external_input::read_skill_parameters(const nlohmann::json& p){
    std::shared_ptr<ConfigSkill_external_input> c = this->get_config<ConfigSkill_external_input>();
    if(!msrm_utils::read_json_param(p,"port_recv",c->port_recv)){
        msrm_utils::print_error("Missing parameter: port_recv");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"port_dst",c->port_dst)){
        msrm_utils::print_error("Missing parameter: port_dst");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"ip_dst",c->ip_dst)){
        msrm_utils::print_error("Missing parameter: ip_dst");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"input_frequency",c->input_frequency)){
        msrm_utils::print_error("Missing parameter: input_frequency");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"mode",c->mode)){
        msrm_utils::print_error("Missing parameter: mode");
        return false;
    }
    return true;
}
void external_input::build_primitives(const Percept& p){
    this->insert_mp<mp_external>("input",p);
    this->set_init_mp("input");

    std::shared_ptr<ConfigSkill_external_input> c_skill = std::static_pointer_cast<ConfigSkill_external_input>(this->_config);
    std::shared_ptr<ConfigMP_mp_external> c_input = std::static_pointer_cast<ConfigMP_mp_external>(this->get_mp("input")->get_config());
    c_input->port_recv=c_skill->port_recv;
    c_input->port_dst=c_skill->port_dst;
    c_input->ip_dst=c_skill->ip_dst;
    c_input->input_frequency=c_skill->input_frequency;
    if(c_skill->mode=="Torque"){
        c_input->mode=InputMode::Torque;
    }
    if(c_skill->mode=="CartesianVelocity"){
        c_input->mode=InputMode::CartesianVelocity;
    }
    if(c_skill->mode=="JointVelocity"){
        c_input->mode=InputMode::JointVelocity;
    }
    if(c_skill->mode=="CartesianPosition"){
        c_input->mode=InputMode::CartesianPosition;
    }
    if(c_skill->mode=="JointPosition"){
        c_input->mode=InputMode::JointPosition;
    }
}
std::tuple<bool,std::string> external_input::check_edges(const Percept& p){
    return std::tuple<bool,std::string>(false,"");
}
bool external_input::check_local_suc_conditions(const Percept& p){
    return false;
}
void external_input::evaluate(){

}
void external_input::create_config(){
    this->_config=std::make_shared<ConfigSkill_external_input>();
}
}
