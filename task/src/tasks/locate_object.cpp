#include "tasks/locate_object.hpp"
#include <chrono>
#include "cpp_utils/network.hpp"
namespace mios{
locate_object::locate_object():Task("locate_object"){
}
locate_object::~locate_object(){
}
void locate_object::initialize_task(){
    this->create_skill(new move_to_pose_joint(),"move");
    this->create_skill(new move_to_pose(),"approach");
}
void locate_object::execute_task(){

    std::vector<std::string> poses=this->search_poses;
    std::chrono::milliseconds ms = std::chrono::duration_cast< std::chrono::milliseconds >(
        std::chrono::system_clock::now().time_since_epoch()
    );
    srand(ms.count());
    unsigned selector=rand()%3;
    this->get_skill("move")->set_object("loc_goal",this->search_poses[selector]);
    std::cout<<"pose1: "<<this->search_poses[selector]<<std::endl;
    this->execute_skill("move");
    usleep(0.5 + static_cast <float> (rand()) /( static_cast <float> (RAND_MAX/(1.5-0.5)))*100000);
    selector=3+rand()%3;
    this->get_skill("move")->set_object("loc_goal",this->search_poses[selector]);
    std::cout<<"pose2: "<<this->search_poses[selector]<<std::endl;
    this->execute_skill("move");
    usleep(0.5 + static_cast <float> (rand()) /( static_cast <float> (RAND_MAX/(1.5-0.5)))*100000);

    this->get_skill("approach")->set_object("loc_goal",this->object);
    this->execute_skill("approach");


//    std::random_shuffle(poses.begin(),poses.end());



//    for(unsigned i=0;i<poses.size();i++){
//        this->get_skill("move")->set_object("loc_goal",poses[i]);
//        this->execute_skill("move");
//        nlohmann::json request,response;
//        request["ID"]=26;
//        cpp_utils::rpc_call("http://10.162.15.69:8910","check_detected",request,response);
//        bool detected;
//        cpp_utils::read_json_param(response["detected"],detected);
//        if(detected){
//            this->get_skill("approach")->set_object("loc_goal",this->object);
//            this->execute_skill("approach");
//            return;
//        }
//    }



}
const EvalTask& locate_object::evaluate_task(){
    return this->_eval_task;
}
bool locate_object::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"object",this->object)){
        cpp_utils::print_error("Missing parameters: object");
        return false;
    }
    if(!cpp_utils::read_json_param(params,"pose_failsafe",this->pose_failsafe)){
        this->pose_failsafe="none";
    }
    if(!cpp_utils::read_json_param<std::string>(params,"search_poses",this->search_poses)){
        this->search_poses.resize(0);
    }
    return true;
}
}
