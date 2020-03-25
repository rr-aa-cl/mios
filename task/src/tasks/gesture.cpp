#include "tasks/gesture.hpp"
namespace mios{
gesture::gesture():Task("gesture"){
}
gesture::~gesture(){
}
void gesture::initialize_task(){
    this->create_skill(std::shared_ptr<gesture_haptic>(new gesture_haptic()),"gesture");
}
void gesture::execute_task(){

    std::static_pointer_cast<Config_gesture_haptic>(this->get_skill("gesture")->get_config())->F_trigger(this->direction)=this->F_thr;

    this->execute_skill("gesture");
}
const EvalTask& gesture::evaluate_task(){
    this->_eval_task.results=this->get_skill("gesture")->get_eval().results;
    return this->_eval_task;
}
bool gesture::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"direction",this->direction)){
        this->direction=0;
    }
    if(!cpp_utils::read_json_param(params,"F_thr",this->F_thr)){
        this->F_thr=0;
    }
return true;
}
}
