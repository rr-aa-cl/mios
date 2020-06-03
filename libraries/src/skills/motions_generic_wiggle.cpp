#include "skills/motions_generic_wiggle.hpp"
#include "strategies/twist_wiggle_strategy.hpp"

namespace mios {

bool SkillParametersGenericWiggleMotion::read_parameters(const nlohmann::json &parameters){
    msrm_utils::read_json_param<double,6,1>(parameters,"dX_fourier_a_a",dX_fourier_a_a);
    msrm_utils::read_json_param<double,6,1>(parameters,"dX_fourier_b_a",dX_fourier_b_a);
    msrm_utils::read_json_param<double,6,1>(parameters,"dX_fourier_a_f",dX_fourier_a_f);
    msrm_utils::read_json_param<double,6,1>(parameters,"dX_fourier_b_f",dX_fourier_b_f);
    msrm_utils::read_json_param<double,6,1>(parameters,"dX_fourier_a_phi",dX_fourier_a_phi);
    msrm_utils::read_json_param<double,6,1>(parameters,"dX_fourier_b_phi",dX_fourier_b_phi);
    msrm_utils::read_json_param(parameters,"use_EE",use_EE);
    msrm_utils::read_json_param(parameters,"tap_to_finish",tap_to_finish);
    return true;
}

GenericWiggleMotion::GenericWiggleMotion(const std::string &id, Memory *memory, const Percept &p):Skill("GenericWiggleMotion",{"goal_pose"},id,memory,p){
}

std::shared_ptr<ManipulationPrimitive> GenericWiggleMotion::get_initial_mp(const Percept &p_0){
    std::shared_ptr<SkillParametersGenericWiggleMotion> skill_params = get_parameters<SkillParametersGenericWiggleMotion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wiggle",p_0);
    mp->create_strategy<TwistWiggleStrategy>("s_0",1);
    mp->get_strategy<TwistWiggleStrategy>("s_0")->set_coefficients(skill_params->dX_fourier_a_a,skill_params->dX_fourier_b_a,skill_params->dX_fourier_a_f,
                                                                   skill_params->dX_fourier_b_f,skill_params->dX_fourier_a_phi,skill_params->dX_fourier_b_phi);
    return mp;
}

Eigen::Matrix<double,3,3> GenericWiggleMotion::get_O_R_T_0(const Percept &p) const{
    std::shared_ptr<SkillParametersGenericWiggleMotion> c = read_parameters<SkillParametersGenericWiggleMotion>();
    if(c->use_EE){
        return p.proprioception.TF_T_EE.block<3,3>(0,0);
    }else{
        return Eigen::Matrix<double,3,3>::Zero();
    }
}

bool GenericWiggleMotion::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersGenericWiggleMotion> c = get_parameters<SkillParametersGenericWiggleMotion>();
    if(c->tap_to_finish){
        for(unsigned i=0;i<p.proprioception.K_F_ext_K.rows();i++){
            if(fabs(p.proprioception.K_F_ext_K(i))>m_memory->read_parameters()->user.F_ext_contact(i)){
                return true;
            }
        }
    }
    return false;
}

bool GenericWiggleMotion::check_local_ex_conditions(const Percept &p){
    return true;
}

}
