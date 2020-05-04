#include "tasks/place_object.hpp"
namespace mios{
place_object::place_object():Task("place_object"){
}
void place_object::initialize_task(){
    this->create_subtask<move_to_location>("move");
    this->create_subtask<move_to_cart_pose>("retreat");
}
void place_object::execute_task(){
    if(!this->is_grasping()){
        msrm_utils::print_error("I am not holding anything to place.");
        return;
    }

    Object obj;
    this->_kb->load_object(this->loc_place,obj);
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

    std::cout<<"approach: "<<TF_T_EE_o_approach<<std::endl;
    std::cout<<"retreat: "<<TF_T_EE_o_retreat<<std::endl;

    Object obj_tmp;
    obj_tmp.name="tmp_move";
    obj_tmp.O_T_o=TF_T_EE_o_approach;
    Eigen::Matrix<double,7,1> q;
    q.setZero();

    this->_kb->teach_object("tmp_move",TF_T_EE_o_approach,q);
    obj_tmp.name="tmp_retreat";
    obj_tmp.O_T_o=TF_T_EE_o_retreat;
    this->_kb->teach_object("tmp_retreat",TF_T_EE_o_retreat,q);

    this->loc_intermediate.push_back("tmp_move");
    this->loc_cart[this->loc_cart.size()-1]=true;
    this->loc_cart.push_back(true);

    nlohmann::json parameters;
    msrm_utils::write_json_array(parameters["loc_intermediate"],this->loc_intermediate);
    msrm_utils::write_json_array(parameters["loc_cart"],this->loc_cart);
    parameters["loc_goal"]=this->loc_place;

    if(!this->get_subtask("move")->read_parameters(parameters)){
        return;
    }

    this->execute_subtask("move");

    this->release_object();

    nlohmann::json params_retreat;
    params_retreat["pose"]="tmp_retreat";

    this->get_subtask("retreat")->read_parameters(params_retreat);
    this->execute_subtask("retreat");
}
const EvalTask& place_object::evaluate_task(){
return this->_eval_task;
}
bool place_object::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"loc_place",this->loc_place)){
        msrm_utils::print_error("Missing parameters: loc_place");
        return false;
    }
    if(!msrm_utils::read_json_param<std::string>(params,"loc_intermediate",this->loc_intermediate)){
        this->loc_intermediate.resize(0);
    }
    if(!msrm_utils::read_json_param<int>(params,"loc_cart",this->loc_cart)){
        this->loc_cart.resize(0);
    }
    if(this->loc_cart.size()!=this->loc_intermediate.size()+1){
        msrm_utils::print_error("Size of loc_cart must be the size of loc_intermediate plus one.");
        return false;
    }

    if(this->loc_cart.size()==0){
        msrm_utils::print_error("Size of loc_cart must be at least 1.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,3,1>(params,"Delta_approach",this->Delta_approach)){
        this->Delta_approach.setZero();
        msrm_utils::print_warning("No approach vector was given.");
    }
    if(!msrm_utils::read_json_param<double,3,1>(params,"Delta_retreat",this->Delta_retreat)){
        this->Delta_retreat.setZero();
        msrm_utils::print_warning("No retreat vector was given.");
    }
    return true;
}
}
