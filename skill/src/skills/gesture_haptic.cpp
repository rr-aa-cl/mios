#include "skills/gesture_haptic.hpp"

namespace mios {

gesture_haptic::gesture_haptic():Skill("gesture_haptic"){

}

bool gesture_haptic::read_skill_parameters(const nlohmann::json &p){

    std::shared_ptr<ConfigSkill_gesture_haptic> c = this->get_config<ConfigSkill_gesture_haptic>();
    msrm_utils::read_json_param<double,6,1>(p,"F_trigger",c->F_trigger);
    msrm_utils::read_json_param<int,6,1>(p,"dir_trigger",c->dir_trigger);
    msrm_utils::read_json_param(p,"wait_for_relax",c->wait_for_relax);
    for(unsigned i=0;i<6;i++){
        if(c->F_trigger(i)<0){
            msrm_utils::print_warning("Only absolute values of forces are used. Signs can be determined with the dir_trigger parameter.");
            c->F_trigger(i)=fabs(c->F_trigger(i));
        }
        if(c->dir_trigger(i)<-1 || c->dir_trigger(i)>1){
            msrm_utils::print_error("Force directions for gestures can only be (1,0,-1).");
            return false;
        }
    }
    return true;
}

void gesture_haptic::create_config(){
    this->_config=std::make_shared<ConfigSkill_gesture_haptic>();
}

void gesture_haptic::build_primitives(const Percept &p){
    this->_triggered<<false,false,false,false,false,false;
    this->_confirmed<<false,false,false,false,false,false;
    this->insert_mp<mp_basic>("gesture",p);
    this->set_init_mp("gesture");
}

std::tuple<bool,std::string> gesture_haptic::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

bool gesture_haptic::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_gesture_haptic> c = this->get_config<ConfigSkill_gesture_haptic>();
    if(this->_confirmed.isZero(0)){
        return false;
    }
    for(unsigned i=0;i<6;i++){
        if(c->F_trigger(i)!=0 && this->_confirmed(i)){
            return true;
        }
    }
    return false;
}

bool gesture_haptic::check_local_ex_conditions(const Percept &p){
    return true;
}

void gesture_haptic::evaluate(){
    this->_eval.cost_err=0;
    this->_eval.cost_suc=0;
    std::shared_ptr<ConfigSkill_gesture_haptic> c = this->get_config<ConfigSkill_gesture_haptic>();
    msrm_utils::write_json_array<int,6,1>(this->_eval.results["directions"],c->dir_trigger);
}

void gesture_haptic::auxiliaries(const Percept &p){
    std::shared_ptr<ConfigSkill_gesture_haptic> c = this->get_config<ConfigSkill_gesture_haptic>();
    for(unsigned i=0;i<6;i++){
        if(c->F_trigger(i)==0){
            continue;
        }
        if(p.K_F_ext(i)>c->F_trigger(i)&&c->dir_trigger(i)==1){
            this->_triggered(i)=true;
        }
        if(p.K_F_ext(i)<-c->F_trigger(i)&&c->dir_trigger(i)==-1){
            this->_triggered(i)=true;
        }
        if((p.K_F_ext(i)>c->F_trigger(i) || p.K_F_ext(i)<-c->F_trigger(i)) && c->dir_trigger(i)==0){
            std::cout<<"TRIGGERED"<<std::endl;
            this->_triggered(i)=true;
        }

        if(this->_triggered(i)==true){
            if(c->wait_for_relax){
                this->_confirmed(i)=true;
            }
            if(fabs(p.TF_F_ext(i))<c->F_trigger(i)){
                this->_confirmed(i)=true;
            }
        }
    }
}

}
