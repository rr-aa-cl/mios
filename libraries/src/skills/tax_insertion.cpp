#include "skills/tax_insertion.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/ff_wiggle_strategy.hpp"
#include "strategies/twist_strategy.hpp"
#include "msrm_cpp_utils/math.hpp"

namespace mios {

bool SkillParametersTaxInsertion::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"insertion_speed",insertion_speed)){
        spdlog::error("Parameter insertion_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"insertion_acc",insertion_acc)){
        spdlog::error("Parameter insertion_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"f_max_push",f_max_push)){
        spdlog::error("Parameter f_max_push could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"stuck_dx_thr",stuck_dx_thr)){
        stuck_dx_thr=0.005;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"search_a",search_a)){
        search_a.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"search_f",search_f)){
        search_f.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"DeltaX",DeltaX)){
        DeltaX.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_x",ROI_x)){
        spdlog::error("Parameter ROI_x could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi)){
        spdlog::error("Parameter ROI_phi could not be loaded but is mandatory.");
        return false;
    }

    if(stuck_dx_thr>insertion_speed(0) || stuck_dx_thr<0){
        spdlog::warn("stuck_dx_thr cannot be greater than insertion_speed[0] or smaller than 0.");
        stuck_dx_thr=insertion_speed(0);
    }

    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxInsertion::get_parameter_list(){
    return {{"f_max_push",{}},{"approach_speed",{}},{"approach_acc",{}},{"insertion_speed",{}},{"insertion_acc",{}},{"stuck_dx_thr",{}},{"search_a",{}},{"search_f",{}},{"DeltaX",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxInsertion::TaxInsertion(const std::string &name, Memory *memory,Portal* portal):Skill("TaxInsertion",{"Insertable","Container","Approach"},name,memory,portal,
{ControlMode::mCartTorque}),m_is_stuck(false),m_dx_avg_last(0){
    m_dx_avg_mem.assign(100,0);
}


Eigen::Matrix<double, 3, 3> TaxInsertion::get_O_R_T_0(const Percept &p) const{
    return get_object("Container")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::get_initial_mp(const Percept &p_0){
    return create_approach_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxInsertion::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_insert_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="insert"){
        if(!is_stuck(p)){
            return {};
        }else{
            return create_wiggle_mp(p);
        }
    }
    if(get_active_mp()->get_name()=="wiggle"){
        if(!is_stuck(p)){
            return create_insert_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a_offset = get_object_pose_T("Approach");
    T_a_offset.block<3,3>(0,0)=msrm_utils::eulerRPY_to_mat(skill_params->DeltaX(3),skill_params->DeltaX(4),skill_params->DeltaX(5));
    Eigen::Matrix<double,4,4> T_a = get_object_pose_T("Approach");
    T_a.block<3,3>(0,0)=T_a_offset.block<3,3>(0,0)*T_a.block<3,3>(0,0);
    T_a.block<3,1>(0,3)+=skill_params->DeltaX.block<3,1>(0,0);
    move->set_goal(T_a,skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::create_contact_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    Eigen::Matrix<double,3,1> dir=get_object_pose_T("Container").block<3,1>(0,3)+skill_params->DeltaX.block<3,1>(0,0)-p.proprioception.T_T_EE.block<3,1>(0,3);
    dir/=dir.norm();
    dX_d<<dir*skill_params->insertion_speed(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->insertion_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::create_insert_mp(const Percept &p){
    spdlog::debug("Insertion::create_move_mp");
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("insert",p);
    mp->create_strategy<MoveToPoseStrategy>("orientation",1);
    std::shared_ptr<MoveToPoseStrategy> orientation = mp->get_strategy<MoveToPoseStrategy>("orientation");
    Eigen::Matrix<double,4,4> T_g=get_object_pose_T("Container");
    T_g.block<3,1>(0,3)=p.proprioception.T_T_EE.block<3,1>(0,3);
    orientation->set_goal(T_g,skill_params->insertion_speed,skill_params->insertion_acc);

    mp->create_strategy<TwistStrategy>("position",1);
    m_insert_dir<<get_object_pose_T("Container").block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3),0,0,0;
    m_insert_dir/=m_insert_dir.norm();
    mp->get_strategy<TwistStrategy>("position")->set_TF_dX_d(m_insert_dir*skill_params->insertion_speed(0),skill_params->insertion_acc);

    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::create_wiggle_mp(const Percept &p){
    spdlog::debug("Insertion::create_wiggle_mp");
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wiggle",p);
    mp->create_strategy<FFWiggleStrategy>("wiggle_x",1);
    mp->get_strategy<FFWiggleStrategy>("wiggle_x")->set_coefficients(Eigen::Matrix<double,6,1>::Zero(),skill_params->search_a,
                                                                   Eigen::Matrix<double,6,1>::Zero(),skill_params->search_f,
                                                                   Eigen::Matrix<double,6,1>::Zero(),Eigen::Matrix<double,6,1>::Zero());
    mp->create_strategy<MoveToPoseStrategy>("orientation",1);
    std::shared_ptr<MoveToPoseStrategy> orientation = mp->get_strategy<MoveToPoseStrategy>("orientation");
    Eigen::Matrix<double,4,4> T_g=get_object_pose_T("Container");
    T_g.block<3,1>(0,3)=p.proprioception.T_T_EE.block<3,1>(0,3);
    orientation->set_goal(T_g,skill_params->insertion_speed,skill_params->insertion_acc);

    mp->create_strategy<TwistStrategy>("position",1);
    m_insert_dir<<get_object_pose_T("Container").block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3),0,0,0;
    m_insert_dir/=m_insert_dir.norm();
    mp->get_strategy<TwistStrategy>("position")->set_TF_dX_d(m_insert_dir*skill_params->insertion_speed(0),skill_params->insertion_acc);
    return mp;
}

void TaxInsertion::update_policies(const Percept &p){
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    if(get_active_mp()->get_name()=="insert" || get_active_mp()->get_name()=="wiggle"){
        double force_factor=1;
        if(p.proprioception.TF_F_ext_K(2)<skill_params->f_max_push-1){
            force_factor=1;
        }else if(p.proprioception.TF_F_ext_K(2)>skill_params->f_max_push){
            force_factor=0;
        }else{
            force_factor=-p.proprioception.TF_F_ext_K(2)+skill_params->f_max_push;
        }
        get_active_mp()->get_strategy<TwistStrategy>("position")->set_TF_dX_d(m_insert_dir*skill_params->insertion_speed(0)*force_factor,skill_params->insertion_acc);
    }

}

bool TaxInsertion::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Container");
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)>T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    // TODO check for ROI in rotation
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Insertable")->name){
        spdlog::debug("TaxInsertion::check_local_pre_conditions: Have not grasped Insertable");
        return false;
    }
    return true;
}

bool TaxInsertion::check_local_suc_conditions(const Percept &p){
    bool depth = p.proprioception.T_T_EE(2,3)>get_object_pose_T("Container")(2,3)-0.001;
    bool lateral = (p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Container").block<3,1>(0,3)).norm()<0.004;
    return depth && lateral;
}

bool TaxInsertion::check_local_ex_conditions(const Percept &p){
    return true;
}

bool TaxInsertion::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxInsertion>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxInsertion>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Container").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Container").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

double TaxInsertion::get_goal_heuristic(const Percept &p){
    return (get_result().p_1.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Container").block<3,1>(0,3)).norm();
}

bool TaxInsertion::is_stuck(const Percept &p){
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
    if(!m_is_stuck && m_dx_avg<get_parameters<SkillParametersTaxInsertion>()->stuck_dx_thr-get_parameters<SkillParametersTaxInsertion>()->stuck_dx_thr*0.1){
        m_is_stuck=true;
        return true;
    }else if(m_is_stuck && m_dx_avg>get_parameters<SkillParametersTaxInsertion>()->stuck_dx_thr+get_parameters<SkillParametersTaxInsertion>()->stuck_dx_thr*0.1){
        m_is_stuck=false;
        return false;
    }
    return m_is_stuck;
}


}
