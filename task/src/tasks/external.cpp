#include "tasks/external.hpp"
namespace mios{
external::external():Task("external"){
}
void external::initialize_task(){
    this->create_skill<external_input>("external_input");
}
void external::execute_task(){
    std::static_pointer_cast<ConfigSkill_external_input>(this->get_skill("external_input")->get_config())->mode=this->mode;
    this->execute_skill("external_input");
}
const EvalTask& external::evaluate_task(){
return this->_eval_task;
}
bool external::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"mode",this->mode)){
        this->mode="Torque";
    }
    return true;
}
}
