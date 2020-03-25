#include "tasks/handover_object.hpp"

namespace mios {

handover_object::handover_object():Task("handover_object"){
}
handover_object::~handover_object(){
}
void handover_object::initialize_task(){
    this->create_skill(new gesture_haptic(),"handover");
}
void handover_object::execute_task(){

    static_cast<Config_gesture_haptic*>(this->get_skill("handover")->get_config())->wait_for_relax=this->wait_for_relax;
    if(!this->is_grasping()){
        this->move_gripper(0.07,2);
        this->execute_skill("handover");
        if(this->get_skill("handover")->get_eval().success){
            if(!this->grasp_object(this->_object)){
                this->_eval_task.success=false;
                return;
            }
        }
    }else{
        this->execute_skill("handover");
        if(this->get_skill("handover")->get_eval().success){
            if(!this->release_object()){
                this->_eval_task.success=false;
                return;
            }
        }
    }
    this->_eval_task.success=true;

}
const EvalTask& handover_object::evaluate_task(){
    this->_eval_task.cost_suc=0;
    this->_eval_task.cost_err=0;
    return this->_eval_task;
}

bool handover_object::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"object",this->_object)){
        cpp_utils::print_error("Missing parameter: object");
        return false;
    }
    if(!cpp_utils::read_json_param(params,"wait_for_relax",this->wait_for_relax)){
        cpp_utils::print_error("Missing parameter: wait_for_relax");
        return false;
    }
    return true;
}

}
