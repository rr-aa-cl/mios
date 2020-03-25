#include "tasks/rehab_task.hpp"
namespace mios{
rehab_task::rehab_task():Task("rehab_task"){
}
rehab_task::~rehab_task(){
}
void rehab_task::initialize_task(){
    this->create_skill(new move_to_pose_joint(),"init");
    this->create_skill(new gesture_haptic(),"gest");
    this->create_skill(new rehab(),"rehab_skill");

    this->_rehabPattern = std::shared_ptr<pattern_rehab>(new pattern_rehab);


}
void rehab_task::execute_task(){


    this->get_skill("rehab_skill")->set_object("start_pose","start_pose");
    this->get_skill("rehab_skill")->set_object("end_pose","end_pose");

    //INIT LEDs
    Eigen::Matrix<double,4,4> start_pose;
    Eigen::Matrix<double,4,4> end_pose;
    start_pose = this->get_skill("rehab_skill")->get_object_pose("start_pose");
    end_pose = this->get_skill("rehab_skill")->get_object_pose("end_pose");
    this->_rehabPattern->set_poses(start_pose, end_pose);

    this->get_skill("init")->set_object("loc_goal","start_pose");
    if(this->pose=="none"){
        static_cast<Config_move_to_pose_joint*>(this->get_skill("init")->get_config())->q_g=this->q_g;
    }
    this->execute_skill("init");
    this->load_led_pattern(this->_rehabPattern);


    while(true){
       // this->execute_skill("gest");
        if(!this->get_stop_flag()){
       //     this->grasp_object("arm");
        }

        static_cast<ConfigSkill_rehab*>(this->get_skill("rehab_skill")->get_config())->stiffness=this->stiffness;
        static_cast<ConfigSkill_rehab*>(this->get_skill("rehab_skill")->get_config())->speed=this->speed;
        static_cast<ConfigSkill_rehab*>(this->get_skill("rehab_skill")->get_config())->motion=this->motion;



        this->execute_skill("rehab_skill");
        if(this->get_skill("rehab_skill")->get_eval().success==false && !this->get_stop_flag()){

         //   this->move_gripper(20,0.08);
           // static_cast<Config_gesture_haptic*>(this->get_skill("gest")->get_config())->time_max=10;
          //  this->execute_skill("gest");
            if(this->get_skill("gest")->get_eval().success==false){
                break;
            }else{
                this->get_skill("init")->set_object("loc_goal","start_pose");
                if(this->pose=="none"){
                    static_cast<Config_move_to_pose_joint*>(this->get_skill("init")->get_config())->q_g=this->q_g;
                }
                this->execute_skill("init");
                continue;
            }
        }
        if(this->get_stop_flag()){

            //            if(this->get_stop_flag()){
            //                this->_core->set_plan_stop(false);
            //            }

            // this->move_gripper(20,0.08); In App-Server ausgelagert

            break;
        }
    }

}
const EvalTask& rehab_task::evaluate_task(){
    return this->_eval_task;
}

bool rehab_task::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params["pose"],this->pose)){
        this->pose="none";
    }
    if(!cpp_utils::read_json_param<double,7,1>(params["q_g"],this->q_g) && this->pose=="none"){
        cpp_utils::print_error("Missing parameters: pose or q_g");
        return false;
    }

    if(!cpp_utils::read_json_param(params["stiffness"],this->stiffness)){
        cpp_utils::print_error("Missing parameter: stiffness");
        this->stiffness=800.0;
    }

    if(!cpp_utils::read_json_param(params["speed"],this->speed)){
        cpp_utils::print_error("Missing parameter: speed");
        this->speed=0.5;
    }

    if(!cpp_utils::read_json_param(params["motion"],this->motion)){
        cpp_utils::print_error("Missing parameter: motion");
        this->motion="circle";
    }

    return true;
}

}
