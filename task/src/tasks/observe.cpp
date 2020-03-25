#include "tasks/observe.hpp"
namespace mios{
observe::observe():Task("observe"){
}
observe::~observe(){
}
void observe::initialize_task(){
    this->create_skill(new move_to_pose_joint(),"move");
    this->create_skill(new motions_generic_wiggle(),"watch");
}
void observe::execute_task(){

    this->load_led_pattern(std::shared_ptr<pattern_interactive>(new pattern_interactive));
    int last_pose=-1;
    while(!this->get_stop_flag()){
        if(this->watch_poses.size()>1){
            unsigned selector_pose = rand() % this->watch_poses.size();
            if(selector_pose!=last_pose){
                this->get_skill("move")->set_object("loc_goal",this->watch_poses[selector_pose]);
                this->execute_skill("move");
                last_pose=selector_pose;
            }
        }else if(this->watch_poses.size()==1){
            this->get_skill("move")->set_object("loc_goal",this->watch_poses[0]);
            this->execute_skill("move");
        }
        Config_motions_generic_wiggle* c_watch = static_cast<Config_motions_generic_wiggle*>(this->get_skill("watch")->get_config());
        c_watch->frames.O_R_TF=Eigen::Matrix<double,3,3>::Identity();
        double t_period = 1./(c_watch->dX_fourier_b_f(2));
        srand(time(0));
        if(this->watch_poses.size()>1){
            c_watch->time_max=t_period+rand() % 5 +1;
        }else{
            c_watch->time_max=1000;
        }
        //        c_watch->time_max=3.0 + static_cast <float> (rand()) /( static_cast <float> (RAND_MAX/(6.0-3.0)));
        this->execute_skill("watch");
        if(this->get_skill("watch")->get_eval().success){
            break;
        }
    }

}
const EvalTask& observe::evaluate_task(){
    return this->_eval_task;
}
bool observe::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"watch_poses",this->watch_poses)){
        this->watch_poses.resize(0);
    }
    return true;
}
}
