#include "skills/move_to_pose_cart.hpp"

namespace mios {

move_to_pose_cart::move_to_pose_cart():Skill("move_to_pose_cart"){
    this->_t_settle=0;
}

bool move_to_pose_cart::read_skill_parameters(const nlohmann::json &p){

    std::shared_ptr<ConfigSkill_move_to_pose_cart> c = std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->_config);
    msrm_utils::read_json_param<double,1,1>(p,"speed",c->speed);
    msrm_utils::read_json_param<double,1,1>(p,"acc",c->acc);
    msrm_utils::read_json_param<double,4,4>(p,"TF_g_offset",c->TF_g_offset);

    if(!msrm_utils::read_json_param<double,4,4>(p,"TF_T_EE_g",c->TF_T_EE_g)){
        msrm_utils::print_error("Parameter TF_T_EE_g could not be loaded but is mandatory.");
        return false;
    }

    msrm_utils::read_json_param(p,"t_settle",c->t_settle);
    return true;
}

void move_to_pose_cart::create_config(){
    this->_config=std::make_shared<ConfigSkill_move_to_pose_cart>();
}

void move_to_pose_cart::build_primitives(const Percept &p){
    this->insert_mp<mp_basic>("move_to_pose",p);
    this->set_init_mp("move_to_pose");

    std::shared_ptr<ConfigMP_mp_basic> c_move_to_pose = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("move_to_pose")->get_config());

    std::shared_ptr<ConfigSkill_move_to_pose_cart> c = std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->_config);

    c_move_to_pose->dX_d<<c->speed(0)*c->user.dX_max(0),c->speed(0)*c->user.dX_max(1);
    c_move_to_pose->ddX_d<<c->acc(0)*c->user.ddX_max(0),c->acc(0)*c->user.ddX_max(1);

    std::shared_ptr<AttractorBasic> attr_move_to_pose=std::static_pointer_cast<AttractorBasic>(this->get_mp("move_to_pose")->get_attractor());
    attr_move_to_pose->attr_vel<<0,0,0,0,0,0;
    if(this->get_object("loc_goal").name=="none"){
        attr_move_to_pose->attr_pose=c->TF_T_EE_g;
    }else{
        attr_move_to_pose->attr_pose=this->get_object_pose("loc_goal");
    }
    Eigen::Matrix<double,3,3> R_tmp=c->TF_g_offset.block<3,3>(0,0)*attr_move_to_pose->attr_pose.block<3,3>(0,0);
    Eigen::Matrix<double,3,1> x_tmp=attr_move_to_pose->attr_pose.block<3,1>(0,3)+c->TF_g_offset.block<3,1>(0,3);
    attr_move_to_pose->attr_pose=msrm_utils::concatenate_matrix(R_tmp,x_tmp);
}

std::tuple<bool,std::string> move_to_pose_cart::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"move_to_pose");
}

bool move_to_pose_cart::check_local_suc_conditions(const Percept &p){
    if(this->get_mp("move_to_pose")->in_attractor(p) && !this->_flag_settle){
        this->_flag_settle=true;
    }
    if(this->_flag_settle){
        this->_t_settle+=0.001;
    }
    return this->get_mp("move_to_pose")->in_attractor(p);
}

bool move_to_pose_cart::check_local_ex_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_move_to_pose_cart> c = std::static_pointer_cast<ConfigSkill_move_to_pose_cart>(this->_config);
    return this->_t_settle>c->t_settle;
}

void move_to_pose_cart::evaluate(){
    this->_eval.cost_err=this->_eval.p_1.time-this->_eval.p_0.time;
    this->_eval.cost_suc=0;
}

}
