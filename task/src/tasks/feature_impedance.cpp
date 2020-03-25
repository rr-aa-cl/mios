#include "tasks/feature_impedance.hpp"

namespace mios {

feature_impedance::feature_impedance():Task("feature_impedance"){
}
void feature_impedance::initialize_task(){
    this->create_skill<move_to_pose_joint>("move");
    this->create_skill<hold_pose>("hold");
}
void feature_impedance::execute_task(){
    while(!this->get_stop_flag()){
        this->get_skill("move")->set_object("loc_goal",this->pose_init);
        this->execute_skill("move");
        this->get_skill("hold")->get_config()->controller.K_0=this->K;
        this->get_skill("hold")->get_config()->controller.xi<<0.7,0.7,0.7,0.7,0.7,0.7;
        this->execute_skill("hold");
    }
}
const EvalTask &feature_impedance::evaluate_task(){
    this->_eval_task.cost_suc=0;
    this->_eval_task.cost_err=0;
    this->_eval_task.success=true;
    return this->_eval_task;
}

bool feature_impedance::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"pose_init",this->pose_init)){
        cpp_utils::print_error("Missing parameter: pose_init");
        return false;
    }
    if(!cpp_utils::read_json_param<double,6,1>(params,"K",this->K)){
        cpp_utils::print_error("Missing parameter: K [6x1]");
        return false;
    }
    return true;
}

}
