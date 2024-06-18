#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/skills/tax_move.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mios/strategies/gripper_strategy.hpp"

namespace mios {

bool SkillParametersTaxMove::from_json(const nlohmann::json &parameters){
    spdlog::trace("SkillParametersTaxMove::from_json");

    bool object_set=false;
    if(!parameters["objects"].is_null()){
        if(parameters["objects"].find("GoalPose")!=parameters["objects"].end()){
            object_set=true;
        }
    }

    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p0"],"dX_d",p0.dX_d)){
            spdlog::error("Missing parameter: p0.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p0"],"ddX_d",p0.ddX_d)){
            spdlog::error("Missing parameter: p0.ddX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,4,4>(parameters["p0"],"T_T_EE_g_offset",p0.T_T_EE_g_offset)){
            p0.T_T_EE_g_offset.setIdentity();
        }
        if(!mirmi_utils::read_json_param<double,4,4>(parameters["p0"],"T_T_EE_g",p0.T_T_EE_g) && !object_set){
            spdlog::error("Missing parameter: p0.T_T_EE_g or GoalPose object.");
            return false;
        }
        if(!mirmi_utils::read_json_param(parameters["p0"],"finger_width",p0.finger_width)){
            p0.finger_width=-1;
        }
        if(!mirmi_utils::read_json_param(parameters["p0"],"finger_speed",p0.finger_speed)){
            p0.finger_speed=0;
        }
        if(!mirmi_utils::read_json_param(parameters["p0"],"t_settle",p0.t_settle)){
            p0.t_settle=0;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxMove::get_parameter_list(){
    return {{"p0",{"dX_d","ddX_d","K_x","t_settle","T_T_EE_g","T_T_EE_g_offset","finger_width","finger_speed"}}};
}

TaxMove::TaxMove(const std::string &id, Memory *memory, Portal *portal):Skill("TaxMove",{"GoalPose"},id,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}),
m_finished(false){
}

std::shared_ptr<ManipulationPrimitive> TaxMove::get_initial_mp(const Percept &p_0){
    return create_move_mp(p_0);
}

std::shared_ptr<ManipulationPrimitive> TaxMove::create_move_mp(const Percept &p){
    spdlog::trace("TaxMove::create_move_mp");
    std::shared_ptr<SkillParametersTaxMove> skill_params = get_parameters<SkillParametersTaxMove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);  
    if(this->get_object("GoalPose")->name=="NullObject"){
        m_T_T_EE_g=skill_params->p0.T_T_EE_g;
    }else{
        m_T_T_EE_g=get_object_pose_T("GoalPose");
    }
    m_T_T_EE_g.block<3,1>(0,3)+=skill_params->p0.T_T_EE_g_offset.block<3,1>(0,3);
    m_T_T_EE_g.block<3,3>(0,0)=skill_params->p0.T_T_EE_g_offset.block<3,3>(0,0)*m_T_T_EE_g.block<3,3>(0,0);
    mp->get_strategy<MoveToPoseStrategy>("move")->set_goal(m_T_T_EE_g,skill_params->p0.dX_d,skill_params->p0.ddX_d);
  
    Eigen::Matrix<double,2,1> scale;
    scale<<1,1;
    mp->get_strategy<MoveToPoseStrategy>("move")->set_scale(scale);
    
    if(skill_params->p0.finger_width!=-1 || skill_params->p0.finger_speed!=0){
        mp->create_strategy<GripperStrategy>("gripper",1);
        mp->get_strategy<GripperStrategy>("gripper")->move(skill_params->p0.finger_width,skill_params->p0.finger_speed);
    }
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxMove::check_local_suc_conditions(const Percept &p){
    if(get_active_mp()->get_strategy<MoveToPoseStrategy>("move")->finished()){  
        if(!m_finished){
            m_finished=true;
            m_t_finished=std::chrono::high_resolution_clock::now();
        }
        if(is_in_env(m_T_T_EE_g,p)){
            return true;
        }else{
            return false;
        }
    }else{
        return false;
    }
}

bool TaxMove::check_local_ex_conditions(const Percept &p){
    if(std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_t_finished).count()>=get_parameters<SkillParametersTaxMove>()->p0.t_settle*1000){
        return true;
    }else{
        return false;
    }
}

double TaxMove::get_goal_heuristic(const Percept &p){
    return (p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("GoalPose").block<3,1>(0,3)).norm() +
            acos(((get_object_pose_T("GoalPose").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2);
}

}
