#include "tasks/guiding_mode.hpp"
namespace mios{
guiding_mode::guiding_mode():Task("guiding_mode"){
}
guiding_mode::~guiding_mode(){
}
void guiding_mode::initialize_task(){
    this->create_skill(new hand_guiding(),"guiding");
}
void guiding_mode::execute_task(){

    ConfigSkill_hand_guiding* c = static_cast<ConfigSkill_hand_guiding*>(this->get_skill("guiding")->get_config());
    c->dist_walls=this->walls;
    c->fix_dim=this->mode;
    c->use_walls<<1,1,1,1,1,1;

    this->execute_skill("guiding");
}
const EvalTask& guiding_mode::evaluate_task(){
return this->_eval_task;
}
bool guiding_mode::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param<double,6,1>(params,"walls",this->walls)){
        this->walls<<10,-10,10,-10,10,-10;
    }
    if(!cpp_utils::read_json_param<double,6,1>(params,"mode",this->mode)){
        this->mode.setZero();
    }
return true;
}
}
