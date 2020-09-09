#include "skills/generic_wiggle_motion.hpp"
#include "strategies/twist_wiggle_strategy.hpp"

namespace mios {

bool SkillParametersGenericWiggleMotion::from_json(const nlohmann::json &parameters){
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

std::map<std::string, std::set<std::string> > SkillParametersGenericWiggleMotion::get_parameter_list(){
    return {{"dX_fourier_a_a",{}},{"dX_fourier_b_a",{}},{"dX_fourier_a_f",{}},{"dX_fourier_b_f",{}},{"dX_fourier_a_phi",{}},{"dX_fourier_b_phi",{}},{"use_EE",{}},{"tap_to_finish",{}}};
}

GenericWiggleMotion::GenericWiggleMotion(const std::string &id, Memory *memory,Portal* portal):Skill("GenericWiggleMotion",{},id,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){
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
        return p.proprioception.T_T_EE.block<3,3>(0,0);
    }else{
        return Eigen::Matrix<double,3,3>::Identity();
    }
}

bool GenericWiggleMotion::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersGenericWiggleMotion> c = get_parameters<SkillParametersGenericWiggleMotion>();
    if(c->tap_to_finish){
        for(unsigned i=0;i<3;i++){
            if(fabs(p.proprioception.K_F_ext_K(i))>m_memory->read_parameters()->user.F_ext_contact(0)){
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
