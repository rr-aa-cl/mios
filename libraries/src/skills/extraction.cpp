#include "skills/extraction.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/ff_wiggle_strategy.hpp"

namespace mios {

bool SkillParametersExtraction::from_json(const nlohmann::json &parameters){
    msrm_utils::read_json_param<double,2,1>(parameters,"traj_speed",traj_speed);
    msrm_utils::read_json_param(parameters,"F_limit",F_limit);
    msrm_utils::read_json_param<double,6,1>(parameters,"search_a",search_a);
    msrm_utils::read_json_param<double,6,1>(parameters,"search_f",search_f);
    return true;
}

Extraction::Extraction(const std::string &name, Memory *memory, Portal* portal,const Percept &p):Skill("Extraction",{"Extractable,ExtractFrom"},name,memory,portal,p,{ControlMode::mCartTorque}){

}


Eigen::Matrix<double, 3, 3> Extraction::get_O_R_T_0(const Percept &p) const{
    return get_object("ExtractFrom")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> Extraction::get_initial_mp(const Percept &p_0){
    return create_move_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Extraction::graph_transition(const Percept &p){
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

std::shared_ptr<ManipulationPrimitive> Extraction::create_move_mp(const Percept &p){
    std::shared_ptr<SkillParametersExtraction> skill_params = get_parameters<SkillParametersExtraction>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p);
    mp->create_strategy<MoveToPoseStrategy>("s_move",1);
    std::shared_ptr<MoveToPoseStrategy> s_move = mp->get_strategy<MoveToPoseStrategy>("s_move");
    s_move->set_goal(get_object("ExtractFrom")->O_T_OB,skill_params->traj_speed,skill_params->traj_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> Extraction::create_wiggle_mp(const Percept &p){
    std::shared_ptr<SkillParametersExtraction> skill_params = get_parameters<SkillParametersExtraction>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wiggle",p);
    mp->create_strategy<FFWiggleStrategy>("wiggle_x",1);
    mp->get_strategy<FFWiggleStrategy>("wiggle_x")->set_coefficients(Eigen::Matrix<double,6,1>::Zero(),skill_params->search_a,
                                                                   Eigen::Matrix<double,6,1>::Zero(),skill_params->search_f,
                                                                   Eigen::Matrix<double,6,1>::Zero(),Eigen::Matrix<double,6,1>::Zero());
    return mp;
}

bool Extraction::check_local_suc_conditions(const Percept &p){
    bool depth = p.proprioception.TF_T_EE(2,3)>get_object("ExtractFrom")->O_T_OB(2,3)-0.001;
    bool lateral = (p.proprioception.TF_T_EE.block<3,1>(0,3)-get_object("ExtractFrom")->O_T_OB.block<3,1>(0,3)).norm()<0.002;
    return depth && lateral;
}

bool Extraction::check_local_ex_conditions(const Percept &p){
    return true;
}

bool Extraction::check_local_err_conditions(const Percept &p){
    return false;
}

void Extraction::evaluate(){

        double c_err_1=m_memory->read_parameters()->skill->time_max+exp((get_result().p_1.proprioception.TF_T_EE.block<3,1>(0,3)-get_object("ExtractFrom")->O_T_OB.block<3,1>(0,3)).norm()*100)-1;
        double c_suc_1=std::chrono::duration_cast<std::chrono::seconds>(get_result().p_1.time-get_result().p_0.time).count();

        double c_err_2=m_memory->read_parameters()->user.F_ext_max(0)+exp((get_result().p_1.proprioception.TF_T_EE.block<3,1>(0,3)-get_object("ExtractFrom")->O_T_OB.block<3,1>(0,3)).norm()*100)-1;
        double c_suc_2=0;
        if(m_cf1_cnt==0){
            c_suc_2=get_result().cost_err;
        }else{
            c_suc_2=m_cf1_sum_force/m_cf1_cnt;
        }
        msrm_utils::print_critical_error("COST_ERR: " + std::to_string(c_err_1));
        msrm_utils::print_critical_error("COST_SUC: " + std::to_string(c_suc_1));
        write_costs(m_memory->read_parameters()->skill->w_cost_function[0]*c_suc_1+m_memory->read_parameters()->skill->w_cost_function[1]*c_suc_2,
                m_memory->read_parameters()->skill->w_cost_function[0]*c_err_1+m_memory->read_parameters()->skill->w_cost_function[1]*c_err_2);
}

void Extraction::auxiliaries(const Percept &p){
    m_cf1_sum_force+=p.proprioception.K_F_ext_K.block<3,1>(0,0).norm();
    m_cf1_cnt++;
}

bool Extraction::is_stuck(const Percept &p){
    if(m_dx_avg_mem.size()==0 || std::chrono::duration_cast<std::chrono::seconds>(p.time-m_memory->get_live_context()->t_skill).count()<get_parameters<SkillParametersExtraction>()->stuck_t_thr){
        return false;
    }
    m_dx_avg_mem[m_dx_avg_last++]=p.proprioception.TF_dX_EE.block<3,1>(0,0).norm();
    if(m_dx_avg_last==m_dx_avg_mem.size()){
        m_dx_avg_last=0;
    }
    m_dx_avg=std::accumulate(m_dx_avg_mem.begin(),m_dx_avg_mem.end(),0)/m_dx_avg_mem.size();
    if(m_dx_avg<get_parameters<SkillParametersExtraction>()->stuck_dx_thr){
        return true;
    }else{
        return false;
    }
}

}
