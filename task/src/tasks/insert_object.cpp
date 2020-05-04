#include "tasks/insert_object.hpp"

#include "franka/exception.h"
namespace mios {

insert_object::insert_object():Task("insert_object"){
}
insert_object::~insert_object(){
}
void insert_object::initialize_task(){

    this->create_skill<move_to_pose_joint>("approach_joint");
    this->create_skill<move_to_pose_cart>("approach");
    this->create_skill<move_to_contact>("contact");
    this->create_skill<insertion>("insertion");
    this->create_skill<move_to_pose_cart>("realign");
    this->create_skill<extraction>("extraction");
    this->create_skill<motions_generic_wiggle>("motion_success");
    this->create_skill<motions_generic_wiggle>("motion_failure");
}
void insert_object::execute_task(){

    std::string obj_grasped = this->request_percept().mios_state.grasped_object;
    if(this->is_grasping() && obj_grasped!=this->_object){
        msrm_utils::print_warning("I am grasping an object that is not " + this->_object + ", aborting extraction task.");
        this->_eval_task.success=false;
        return;
    }else if(!this->is_grasping()){
        msrm_utils::print_error("I am not holding anything");
        return;
    }


    //    if(this->is_grasping()){
    //        this->grasp_object(this->_object);
    //    }else if(!this->is_grasping()){
    //        msrm_utils::print_error("I am not holding anything");
    //        return;
    //    }

    std::map<std::string,std::array<unsigned,3> > colors;
    colors["far-left"]={0,0,100};
    colors["left"]={0,0,100};
    colors["middle"]={0,0,100};
    colors["right"]={0,0,100};
    colors["far-right"]={0,0,100};
    this->load_led_pattern(std::shared_ptr<pattern_custom>(new pattern_custom(colors)));
    this->get_skill("approach_joint")->set_object("loc_goal",this->_hole);
    this->get_skill("approach")->set_object("loc_goal",this->_hole);
    this->get_skill("contact")->set_object("surface",this->_hole);
    this->get_skill("insertion")->set_object("object",this->_object);
    this->get_skill("insertion")->set_object("hole",this->_hole);
    this->get_skill("extraction")->set_object("object",this->_object);
    this->get_skill("extraction")->set_object("hole",this->_hole);

    Eigen::Matrix<double,3,1> O_phi_init = this->get_skill("insertion")->get_object_pose("hole",false).block<3,3>(0,0)*std::static_pointer_cast<ConfigSkill_insertion>(this->get_skill("insertion")->get_config())->phi_init;
    Eigen::Matrix<double,3,1> O_offset = this->get_skill("insertion")->get_object_pose("hole",false).block<3,3>(0,0)*std::static_pointer_cast<ConfigSkill_insertion>(this->get_skill("insertion")->get_config())->offset_init;
    Eigen::Matrix<double,4,4> O_T_offset=msrm_utils::concatenate_matrix(msrm_utils::eulerRPY_to_mat(O_phi_init(0),O_phi_init(1),O_phi_init(2)),O_offset);

    std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("approach")->get_config())->TF_g_offset=msrm_utils::rotate_matrix(O_T_offset,msrm_utils::invert_matrix(this->get_skill("approach")->get_config()->frames.O_R_TF));

    double d_hole;
    if(!msrm_utils::find_json_value(this->get_skill("insertion")->get_object("hole").geometry,"depth")){
        msrm_utils::print_error("Object "+this->get_skill("insertion")->get_object("hole").name+" has no geometry property <depth>.");
        throw TaskException("Object "+this->get_skill("insertion")->get_object("hole").name+" has no geometry property <depth>.");
    }
    msrm_utils::read_json_param(this->get_skill("insertion")->get_object("hole").geometry,"depth",d_hole);
    Eigen::Matrix<double,3,1> TF_d_hole;
    TF_d_hole<<0,0,d_hole+0.0;
    Eigen::Matrix<double,3,1> O_d_hole=this->get_skill("insertion")->get_object_pose("hole",false).block<3,3>(0,0)*TF_d_hole;
    std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("approach")->get_config())->TF_g_offset(0,3)-=O_d_hole(0);
    std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("approach")->get_config())->TF_g_offset(1,3)-=O_d_hole(1);
    std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("approach")->get_config())->TF_g_offset(2,3)-=O_d_hole(2);
    //    this->get_skill("insertion")->get_config()->config_global.dX_max(0)=0.5;

    std::static_pointer_cast<ConfigSkill_move_to_contact>(this->get_skill("contact")->get_config())->speed(0)=0.05;

    this->set_state("approach");
    if(this->_joint){
        this->execute_skill("approach_joint");
    }
    this->execute_skill("approach");
    if(!this->get_skill("approach")->get_eval().success){
        return;
    }

    this->set_state("contact");
//    this->execute_skill("contact");
    this->set_state("insertion");
    this->execute_skill("insertion");
    if(this->_release && this->get_skill("insertion")->get_eval().success){
        this->release_object();
        Eigen::Matrix<double,3,1> TF_d_hole_release;
        Object o;
        this->_kb->load_object(this->_hole,o);
        double d_hole=0;
        msrm_utils::read_json_param(o.geometry,"d_hole",d_hole);
        this->_kb->load_object(this->_object,o);
        TF_d_hole_release<<0,0,d_hole+o.EE_T_O(2,3)+0.05;
        Eigen::Matrix<double,3,1> O_d_hole_release=this->get_skill("insertion")->get_object_pose("hole",false).block<3,3>(0,0)*TF_d_hole_release;
        std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("approach")->get_config())->TF_g_offset<<1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1;
        //        static_cast<Config_move_to_pose*>(this->get_skill("approach")->get_config())->TF_g_offset(0,3)=0;
        //        static_cast<Config_move_to_pose*>(this->get_skill("approach")->get_config())->TF_g_offset(1,3)=0;
        std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("approach")->get_config())->TF_g_offset(2,3)-=O_d_hole_release(2);
        this->execute_skill("approach");
        return;
    }
    this->set_state("Finished");
    if(this->get_skill("insertion")->get_eval().success){
        this->_kb->set_event("inserted","success");
    }else{
        this->_kb->set_event("inserted","failure");
    }

    return;

    Object o;
    this->_kb->load_object(this->_hole,o);
    if(this->_extract || !this->get_skill("insertion")->get_eval().success){
        this->set_state("extraction");
        while(!this->get_skill("extraction")->get_eval().success && !this->get_stop_flag()){
            std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("realign")->get_config())->TF_T_EE_g=this->_kb->transform_to_EE(o.TF_T_o(this->get_skill("realign")->get_config()->frames.O_R_TF));
            std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->get_skill("realign")->get_config())->TF_T_EE_g.block<3,1>(0,3)=this->request_percept(this->get_skill("realign")->get_config()->frames.O_R_TF).TF_T_EE.block<3,1>(0,3);
            this->execute_skill("realign");
            this->execute_skill("extraction");
        }
    }

    this->set_state("Finished");
    if(this->_emotions){
        if(this->get_skill("insertion")->get_eval().success){
            this->_kb->set_event("inserted","success");
            this->load_led_pattern(std::shared_ptr<pattern_success>(new pattern_success(2)));
            this->execute_skill("motion_success");
            this->execute_skill("approach_joint");
        }else{
            this->_kb->set_event("inserted","failure");
            this->load_led_pattern(std::shared_ptr<pattern_disappointment>(new pattern_disappointment(2)));
            this->execute_skill("motion_failure");
        }
    }
    this->load_led_pattern(std::shared_ptr<pattern_white>(new pattern_white()));
}

void insert_object::recover_task(){
    //    Object o;
    //    this->_kb->load_object(this->_hole,o);
    //    if(this->get_state()=="contact" || this->get_state()=="insertion" || this->get_state()=="extraction"){
    //        while(!this->get_skill("extraction")->get_eval().success && !this->get_stop_flag()){
    //            static_cast<Config_move_to_pose*>(this->get_skill("realign")->get_config())->TF_T_EE_g=this->_kb->transform_to_EE(o.TF_T_o(this->get_skill("realign")->get_config()->frames.O_R_TF));
    //            static_cast<Config_move_to_pose*>(this->get_skill("realign")->get_config())->TF_T_EE_g.block<3,1>(0,3)=this->request_percept(this->get_skill("realign")->get_config()->frames.O_R_TF).TF_T_EE.block<3,1>(0,3);
    //            this->execute_skill("realign");
    //            this->execute_skill("extraction");
    //        }
    //    }
}

const EvalTask& insert_object::evaluate_task(){
    this->_eval_task.cost_suc=this->get_skill("insertion")->get_eval().cost_suc;
    this->_eval_task.cost_err=this->get_skill("insertion")->get_eval().cost_err;
    this->_eval_task.success=this->get_skill("insertion")->get_eval().success;
    return this->_eval_task;
}

bool insert_object::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"release",this->_release)){
        this->_release=false;
    }
    if(!msrm_utils::read_json_param(params,"extract",this->_extract)){
        this->_extract=true;
    }
    //    if(this->_extract && this->_release){
    //        msrm_utils::print_warning("Can not release and extract the object at the same time. Setting extract to false");
    //        this->_extract=false;
    //    }
    if(!msrm_utils::read_json_param(params,"joint",this->_joint)){
        this->_joint=false;
    }
    if(!msrm_utils::read_json_param(params,"emotions",this->_emotions)){
        this->_emotions=false;
    }
    if(!msrm_utils::read_json_param(params,"object",this->_object)){
        msrm_utils::print_error("Specify object to insert.");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"hole",this->_hole)){
        msrm_utils::print_error("Specify hole in which to insert the object.");
        return false;
    }
    if(!this->_extract){
        this->_emotions=false;
    }

    return true;
}


}
