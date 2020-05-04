#include "tasks/extract_object.hpp"

namespace mios {

extract_object::extract_object():Task("extract_object"){
}
void extract_object::initialize_task(){
    this->create_skill<move_to_pose_joint>("approach_joint");
    this->create_skill<move_to_pose_cart>("approach_above");
    this->create_skill<move_to_pose_cart>("approach");
    this->create_skill<move_to_pose_cart>("realign");
    this->create_skill<extraction>("extraction");
}
void extract_object::execute_task(){

    std::string obj_grasped = this->request_percept().mios_state.grasped_object;
    bool grasped=false;
    if(this->is_grasping() && obj_grasped!=this->_object){
        msrm_utils::print_warning("I am already grasping an object that is not " + this->_object + ", aborting extraction task.");
        this->_eval_task.success=false;
        return;
    }
    if(this->is_grasping() && obj_grasped==this->_object){
        msrm_utils::print_success("I am already grasping the object with id " + this->_object + ".");
        this->_eval_task.success=true;
        grasped=true;
    }
    this->get_skill("approach_joint")->set_object("loc_goal",this->_hole);
    this->get_skill("approach_above")->set_object("loc_goal",this->_object);
    this->get_skill("approach")->set_object("loc_goal",this->_object);
    this->get_skill("extraction")->set_object("hole",this->_hole);
    this->get_skill("extraction")->set_object("object",this->_object);
    if(!grasped){

        this->set_state("approach");
        if(this->_joint){
            this->execute_skill("approach_joint");;
        }
        this->execute_skill("approach_above");
        if(!this->get_skill("approach_above")->get_eval().success){
            this->_eval_task.success=false;
            return;
        }
        if(!this->move_gripper(0.06,1)){
            msrm_utils::print_error("Gripper error.");
            this->_eval_task.success=false;
            return;
        }

        this->execute_skill("approach");
        if(!this->get_skill("approach")->get_eval().success){
            this->_eval_task.success=false;
            return;
        }
        Percept p = this->request_percept();
        Object obj;
        this->_kb->load_object(this->_object,obj);

        this->set_state("grasp");
        if(!this->grasp_object(this->_object,-1,1,30,false)){
            this->_eval_task.success=false;
            return;
        }
    }

    Object o;
    this->_kb->load_object(this->_hole,o);
    this->set_state("extraction");
    while(!this->get_skill("extraction")->get_eval().success && !this->get_stop_flag()){
        std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("realign")->get_config())->TF_T_EE_g=this->_kb->transform_to_EE(o.TF_T_o(this->get_skill("realign")->get_config()->frames.O_R_TF));
//        static_cast<Config_move_to_pose*>(this->get_skill("realign")->get_config())->TF_T_EE_g=this->_kb->transform_to_EE(o.TF_T_o(this->get_skill("realign")->get_config()->frames.O_R_TF));
        std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("realign")->get_config())->TF_T_EE_g.block<3,1>(0,3)=this->request_percept(this->get_skill("realign")->get_config()->frames.O_R_TF).TF_T_EE.block<3,1>(0,3);
        this->execute_skill("realign");
        this->execute_skill("extraction");
    }
    this->_eval_task.success=this->get_skill("extraction")->get_eval().success;
}

void extract_object::recover_task(){
    Object o;
    this->_kb->load_object(this->_hole,o);
    if(this->get_state()=="contact" || this->get_state()=="extraction"){
        while(!this->get_skill("extraction")->get_eval().success && !this->get_stop_flag()){
            std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("realign")->get_config())->TF_T_EE_g=this->_kb->transform_to_EE(o.TF_T_o(this->get_skill("realign")->get_config()->frames.O_R_TF));
            std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("realign")->get_config())->TF_T_EE_g.block<3,1>(0,3)=this->request_percept(this->get_skill("realign")->get_config()->frames.O_R_TF).TF_T_EE.block<3,1>(0,3);
            this->execute_skill("realign");
            this->execute_skill("extraction");
        }
    }
}

const EvalTask& extract_object::evaluate_task(){
    this->_eval_task.cost_suc=0;
    this->_eval_task.cost_err=0;
    //    this->_eval_task.success=true;
    return this->_eval_task;
}

bool extract_object::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"joint",this->_joint)){
        this->_joint=false;
    }
    if(!msrm_utils::read_json_param(params,"object",this->_object)){
        msrm_utils::print_error("Specify object to extract.");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"hole",this->_hole)){
        msrm_utils::print_error("Specify hole from which to extract the object.");
        return false;
    }
    return true;
}

}
