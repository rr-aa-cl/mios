#include "skills/move_to_contact.hpp"
#include "strategies/move_to_pose.hpp"
#include "msrm_cpp_utils/math.hpp"

namespace mios {

bool SkillParametersMoveToContact::from_json(const nlohmann::json &p){
    if(!msrm_utils::read_json_param(p,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersMoveToContact::get_parameter_list(){
    return {{"speed",{}}};
}

MoveToContact::MoveToContact(const std::string &id, Memory *memory, Portal* portal):Skill("MoveToContact",{"goal_pose"},id,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){
}

//Eigen::Matrix<double,3,3> MoveToContact::get_O_R_T_0(const Percept &p) const{
//    if(this->get_object("goal_pose")->name!="NullObject"){
//        Eigen::Matrix<double,3,1> object_dir=get_object("goal_pose")->O_T_OB.block<3,1>(0,3)-p.proprioception.O_T_EE.block<3,1>(0,3);
//        Eigen::Matrix<double,3,1> tmp;
//        tmp<<0,0,1;
//        if(object_dir.dot(tmp)<1e-3){
//            tmp<<0,1,0;
//        }
//        return msrm_utils::build_rotation_matrix(object_dir,tmp);
//    }else{
//        throw SkillException("No valid object has been grounded.");
//    }
//}

std::shared_ptr<ManipulationPrimitive> MoveToContact::get_initial_mp(const Percept &p_0){
    std::shared_ptr<SkillParametersMoveToContact> skill_params = get_parameters<SkillParametersMoveToContact>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p_0);
    mp->create_strategy<MoveToPoseStrategy>("s_0",1);

    Eigen::Matrix<double,4,4> T_g;

    if(this->get_object("goal_pose")->name!="NullObject"){
        T_g=msrm_utils::rotate_matrix(get_object("goal_pose")->O_T_OB,m_memory->read_parameters()->frames.O_R_T.transpose());
        T_g.block<3,3>(0,0)=p_0.proprioception.T_T_EE.block<3,3>(0,0);
        Eigen::Matrix<double,3,1> goal_dir=T_g.block<3,1>(0,3)-p_0.proprioception.T_T_EE.block<3,1>(0,3);
        goal_dir.normalize();
        T_g.block<3,1>(0,3)+=goal_dir*0.05;
    }else{
        throw SkillException("No valid object has been grounded.");
    }
    Eigen::Matrix<double,2,1> speed;
    Eigen::Matrix<double,2,1> acc;
    speed<<skill_params->speed,m_memory->read_parameters()->user.dX_default(1);
    acc<<m_memory->read_parameters()->user.ddX_default(0),m_memory->read_parameters()->user.ddX_default(1);
    mp->get_strategy<MoveToPoseStrategy>("s_0")->set_goal(T_g,speed,acc);
    Eigen::Matrix<double,2,1> t_scale;
    t_scale<<1,1;
    mp->get_strategy<MoveToPoseStrategy>("s_0")->set_scale(t_scale);
    return mp;
}

bool MoveToContact::check_local_suc_conditions(const Percept &p){
    for(unsigned i=0;i<3;i++){
        if(fabs(p.proprioception.TF_F_ext_K(i))>m_memory->read_parameters()->user.F_ext_contact(0)){
            return true;
        }
    }
    return false;
}

bool MoveToContact::check_local_ex_conditions(const Percept &p){
    return true;
}

bool MoveToContact::check_local_err_conditions(const Percept &p){
    return get_active_mp()->get_strategy<MoveToPoseStrategy>("s_0")->finished();
}

}
