#include "skills/insertion.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/ff_wiggle_strategy.hpp"

namespace mios {

bool SkillParametersInsertion::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"traj_speed",traj_speed)){
        spdlog::error("Parameter traj_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"traj_acc",traj_acc)){
        spdlog::error("Parameter traj_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"stuck_dx_thr",stuck_dx_thr)){
        spdlog::error("Parameter stuck_dx_thr could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"search_a",search_a)){
        spdlog::error("Parameter search_a could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"search_f",search_f)){
        spdlog::error("Parameter search_f could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_x",ROI_x)){
        spdlog::error("Parameter ROI_x could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi)){
        spdlog::error("Parameter ROI_phi could not be loaded but is mandatory.");
        return false;
    }

    if(stuck_dx_thr>traj_speed(0) || stuck_dx_thr<0){
        spdlog::warn("stuck_dx_thr cannot be greater than traj_speed[0] or smaller than 0.");
        stuck_dx_thr=traj_speed(0);
    }

    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersInsertion::get_parameter_list(){
    return {{"traj_speed",{}},{"traj_acc",{}},{"stuck_dx_thr",{}},{"search_a",{}},{"search_f",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

Insertion::Insertion(const std::string &name, Memory *memory,Portal* portal):Skill("Insertion",{"Insertable","InsertInto"},name,memory,portal,
{ControlMode::mCartTorque}),m_is_stuck(false),m_dx_avg_last(0){
    m_dx_avg_mem.assign(100,0);
}


Eigen::Matrix<double, 3, 3> Insertion::get_O_R_T_0(const Percept &p) const{
    return get_object("InsertInto")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> Insertion::get_initial_mp(const Percept &p_0){
    return create_move_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Insertion::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="move"){
        if(!is_stuck(p)){
            return {};
        }else{
            return create_wiggle_mp(p);
        }
    }
    if(get_active_mp()->get_name()=="wiggle"){
        if(!is_stuck(p)){
            return create_move_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> Insertion::create_move_mp(const Percept &p){
    spdlog::debug("Insertion::create_move_mp");
    std::shared_ptr<SkillParametersInsertion> skill_params = get_parameters<SkillParametersInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p);
    mp->create_strategy<MoveToPoseStrategy>("s_move",1);
    std::shared_ptr<MoveToPoseStrategy> s_move = mp->get_strategy<MoveToPoseStrategy>("s_move");
    s_move->set_goal(get_object_pose_T("InsertInto"),skill_params->traj_speed,skill_params->traj_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> Insertion::create_wiggle_mp(const Percept &p){
    spdlog::debug("Insertion::create_wiggle_mp");
    std::shared_ptr<SkillParametersInsertion> skill_params = get_parameters<SkillParametersInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wiggle",p);
    mp->create_strategy<FFWiggleStrategy>("wiggle_x",1);
    mp->get_strategy<FFWiggleStrategy>("wiggle_x")->set_coefficients(Eigen::Matrix<double,6,1>::Zero(),skill_params->search_a,
                                                                   Eigen::Matrix<double,6,1>::Zero(),skill_params->search_f,
                                                                   Eigen::Matrix<double,6,1>::Zero(),Eigen::Matrix<double,6,1>::Zero());
    mp->create_strategy<MoveToPoseStrategy>("s_move",1);
    std::shared_ptr<MoveToPoseStrategy> s_move = mp->get_strategy<MoveToPoseStrategy>("s_move");
    s_move->set_goal(get_object_pose_T("InsertInto"),skill_params->traj_speed,skill_params->traj_acc);

    Eigen::Matrix<double,2,1> t_scale;
    t_scale<<1,1;
    s_move->set_scale(t_scale);
    return mp;
}

bool Insertion::check_local_suc_conditions(const Percept &p){
    bool depth = p.proprioception.T_T_EE(2,3)>get_object_pose_T("InsertInto")(2,3)-0.001;
    bool lateral = (p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("InsertInto").block<3,1>(0,3)).norm()<0.002;
    return depth && lateral;
}

bool Insertion::check_local_ex_conditions(const Percept &p){
    return true;
}

bool Insertion::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersInsertion>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersInsertion>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("InsertInto").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("InsertInto").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

double Insertion::get_goal_heuristic(const Percept &p){
    return (get_result().p_1.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("InsertInto").block<3,1>(0,3)).norm();
}

void Insertion::auxiliaries(const Percept &p){
    m_cf1_sum_force+=p.proprioception.K_F_ext_K.block<3,1>(0,0).norm();
    m_cf1_cnt++;
}

bool Insertion::is_stuck(const Percept &p){
    m_dx_avg_mem[m_dx_avg_last++]=p.proprioception.TF_dX_EE.block<3,1>(0,0).norm();
    if(m_dx_avg_last==m_dx_avg_mem.size()){
        m_dx_avg_last=0;
    }
    m_dx_avg=0;
    for(unsigned i=0;i<m_dx_avg_mem.size();i++){
        m_dx_avg+=m_dx_avg_mem[i];
    }
    m_dx_avg/=m_dx_avg_mem.size();
//    m_dx_avg=std::accumulate(m_dx_avg_mem.begin(),m_dx_avg_mem.end(),0)/(double)m_dx_avg_mem.size();
    if(!m_is_stuck && m_dx_avg<get_parameters<SkillParametersInsertion>()->stuck_dx_thr-get_parameters<SkillParametersInsertion>()->stuck_dx_thr*0.1){
        m_is_stuck=true;
        return true;
    }else if(m_is_stuck && m_dx_avg>get_parameters<SkillParametersInsertion>()->stuck_dx_thr+get_parameters<SkillParametersInsertion>()->stuck_dx_thr*0.1){
        m_is_stuck=false;
        return false;
    }
    return m_is_stuck;
}

}
