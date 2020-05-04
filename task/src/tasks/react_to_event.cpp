#include "tasks/react_to_event.hpp"
namespace mios{
react_to_event::react_to_event():Task("react_to_event"){
}
void react_to_event::initialize_task(){
    this->create_skill<motions_generic_wiggle>("motion_01");
}
void react_to_event::execute_task(){
    if(this->event=="inserted"){
        std::shared_ptr<ConfigSkill_motions_generic_wiggle> c = std::static_pointer_cast<ConfigSkill_motions_generic_wiggle>(this->get_skill("motion_01")->get_config());
        if(this->_kb->get_event(this->event)=="success"){
            c->time_max=2;
            c->dX_fourier_b_a(2)=0.025;
            c->dX_fourier_b_f(2)=1.5;
            c->dX_fourier_b_phi(2)=1.57;
            this->load_led_pattern(std::shared_ptr<pattern_success>(new pattern_success(2)));
            this->execute_skill("motion_01");
        }else if(this->_kb->get_event(this->event)=="failure"){
            this->load_led_pattern(std::shared_ptr<pattern_disappointment>(new pattern_disappointment(2)));
            c->time_max=2;
            c->dX_fourier_b_a(1)=0.025;
            c->dX_fourier_b_f(1)=1.5;
            c->dX_fourier_b_phi(1)=1.57;
            this->execute_skill("motion_01");
        }
        this->_kb->set_event(this->event,"");
    }

}
const EvalTask& react_to_event::evaluate_task(){
return this->_eval_task;
}
bool react_to_event::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"event",this->event)){
        this->event="none";
    }
return true;
}
}
