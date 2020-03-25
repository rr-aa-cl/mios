#include "tasks/fetch_object.hpp"
namespace mios{
fetch_object::fetch_object():Task("fetch_object"){
}
fetch_object::~fetch_object(){
}
void fetch_object::initialize_task(){
    this->create_subtask(new move_to_location(),"move");
    this->create_subtask(new move_to_cart_pose(),"retreat");
}
void fetch_object::execute_task(){

    if(this->is_grasping()){
        cpp_utils::print_error("I am already holding something.");
        return;
    }
    this->move_gripper(0.05,0.02);

    Object obj;
    this->_kb->load_object(this->object,obj);
    Eigen::Matrix<double,4,4> TF_T_EE_o = this->_kb->transform_to_EE(obj.O_T_o);
    //    Eigen::Matrix<double,4,4> TF_T_EE_o = obj.O_T_o;
    Eigen::Matrix<double,4,4> TF_T_EE_o_approach=TF_T_EE_o;
    Eigen::Matrix<double,4,4> TF_T_EE_o_retreat=TF_T_EE_o;

    TF_T_EE_o_approach(0,3)+=this->Delta_approach(0);
    TF_T_EE_o_approach(1,3)+=this->Delta_approach(1);
    TF_T_EE_o_approach(2,3)+=this->Delta_approach(2);

    TF_T_EE_o_retreat(0,3)+=this->Delta_retreat(0);
    TF_T_EE_o_retreat(1,3)+=this->Delta_retreat(1);
    TF_T_EE_o_retreat(2,3)+=this->Delta_retreat(2);

    Object obj_tmp;
    obj_tmp.name="tmp_approach";
    obj_tmp.O_T_o=TF_T_EE_o_approach;
    Eigen::Matrix<double,7,1> q;
    q.setZero();

    this->_kb->teach_object("tmp_approach",TF_T_EE_o_approach,q);

    obj_tmp.name="tmp_retreat";
    obj_tmp.O_T_o=TF_T_EE_o_retreat;
    this->_kb->teach_object("tmp_retreat",TF_T_EE_o_retreat,q);

    this->loc_intermediate.push_back("tmp_approach");
    this->loc_cart[this->loc_cart.size()-1]=true;
    this->loc_cart.push_back(true);

    nlohmann::json parameters;
    cpp_utils::write_json_array(parameters["loc_intermediate"],this->loc_intermediate);
    cpp_utils::write_json_array(parameters["loc_cart"],this->loc_cart);
    parameters["loc_goal"]=this->object;

    if(!this->get_subtask("move")->read_parameters(parameters)){
        return;
    }

    this->execute_subtask("move");

    if(!this->grasp_object(this->object)){
        cpp_utils::print_error("Could not grasp");
    }

    nlohmann::json params_retreat;
    params_retreat["pose"]="tmp_retreat";

    this->get_subtask("retreat")->read_parameters(params_retreat);
    this->execute_subtask("retreat");


}
const EvalTask& fetch_object::evaluate_task(){
    return this->_eval_task;
}
bool fetch_object::read_parameters(const nlohmann::json& params){
    if(!cpp_utils::read_json_param(params,"object",this->object)){
        cpp_utils::print_error("Missing parameters: object");
        return false;
    }
    if(!cpp_utils::read_json_param<std::string>(params,"loc_intermediate",this->loc_intermediate)){
        this->loc_intermediate.resize(0);
    }
    if(!cpp_utils::read_json_param<int>(params,"loc_cart",this->loc_cart)){
        this->loc_cart.resize(0);
    }
    if(this->loc_cart.size()!=(this->loc_intermediate.size()+1)){
        cpp_utils::print_error("Size of loc_cart must be the size of loc_intermediate plus one.");
        return false;
    }

    if(this->loc_cart.size()==0){
        cpp_utils::print_error("Size of loc_cart must be at least 1.");
        return false;
    }

    if(!cpp_utils::read_json_param<double,3,1>(params,"Delta_approach",this->Delta_approach)){
        this->Delta_approach.setZero();
        cpp_utils::print_warning("No approach vector was given.");
    }
    if(!cpp_utils::read_json_param<double,3,1>(params,"Delta_retreat",this->Delta_retreat)){
        this->Delta_retreat.setZero();
        cpp_utils::print_warning("No retreat vector was given.");
    }
    return true;
}
}
