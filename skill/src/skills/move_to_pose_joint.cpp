#include "skills/move_to_pose_joint.hpp"

namespace mios {

move_to_pose_joint::move_to_pose_joint():Skill("move_to_pose_joint"){
}

move_to_pose_joint::~move_to_pose_joint(){

}

bool move_to_pose_joint::read_skill_parameters(const nlohmann::json &p){
    std::shared_ptr<ConfigSkill_move_to_pose_joint> c = this->get_config<ConfigSkill_move_to_pose_joint>();
    cpp_utils::read_json_param<double,1,1>(p,"speed",c->speed);
    cpp_utils::read_json_param<double,1,1>(p,"acc",c->acc);
    cpp_utils::read_json_param<double,7,1>(p,"q_g_offset",c->q_g_offset);

    if(!cpp_utils::read_json_param<double,7,1>(p,"q_g",c->q_g)){
        cpp_utils::print_error("Parameter q_g could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

void move_to_pose_joint::create_config(){
    this->_config=std::make_shared<ConfigSkill_move_to_pose_joint>();
}

void move_to_pose_joint::build_primitives(const Percept &p){
    this->insert_mp<mp_basic_joint>("move_to_pose_joint",p);
    this->set_init_mp("move_to_pose_joint");

    std::shared_ptr<ConfigMP_mp_basic_joint> c_move_to_pose_joint = std::static_pointer_cast<ConfigMP_mp_basic_joint>(this->get_mp("move_to_pose_joint")->get_config());

    std::shared_ptr<ConfigSkill_move_to_pose_joint> c = std::static_pointer_cast<ConfigSkill_move_to_pose_joint>(this->_config);

    c_move_to_pose_joint->dq_d<<c->speed(0)*c->user.dq_max(0);
    c_move_to_pose_joint->ddq_d<<c->acc(0)*c->user.ddq_max(0);

    std::shared_ptr<AttractorBasicJoint> attr_move_to_pose_joint = std::static_pointer_cast<AttractorBasicJoint>(this->get_mp("move_to_pose_joint")->get_attractor());
    attr_move_to_pose_joint->attr_vel<<0,0,0,0,0,0,0;
    if(this->get_object("loc_goal").name=="none"){
        attr_move_to_pose_joint->attr_pose=c->q_g;
    }else{
        attr_move_to_pose_joint->attr_pose=this->get_object("loc_goal").q_o;
    }

    attr_move_to_pose_joint->attr_pose=attr_move_to_pose_joint->attr_pose+c->q_g_offset;
}

std::tuple<bool,std::string> move_to_pose_joint::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"move_to_pose_joint");
}

bool move_to_pose_joint::check_local_suc_conditions(const Percept &p){
    return this->get_mp("move_to_pose_joint")->in_attractor(p);
}

bool move_to_pose_joint::check_local_ex_conditions(const Percept &p){
    return true;
}

void move_to_pose_joint::evaluate(){
    this->_eval.cost_err=this->_eval.p_1.time-this->_eval.p_0.time;
    this->_eval.cost_suc=0;
}

}
