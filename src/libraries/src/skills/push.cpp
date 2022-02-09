#include "mios/skills/push.hpp"
//#include "mios/strategies/desired_wrench_strategy.hpp"
#include "mios/strategies/ff_strategy.hpp"
#include "msrm_cpp_utils/math/math.hpp"

namespace mios{

bool SkillParametersPush::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,3,1>(parameters,"F_push",F_push)){
        spdlog::error("Parameter F_push could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,3,1>(parameters,"DX_max",DX_max)){
        spdlog::error("Parameter DX_max could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"duration",duration)){
        spdlog::error("Parameter duration could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersPush::get_parameter_list(){
    return {{"F_push",{}},{"DX_max",{}},{"duration",{}}};
}

Push::Push(const std::string& name, Memory* memory, Portal *portal):Skill("Push",{"pushable"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> Push::get_O_R_T_0(const Percept &p) const{
    return get_object("pushable")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> Push::get_initial_mp(const Percept& p){
    m_TF_T_EE_0=p.proprioception.T_T_EE;

    std::shared_ptr<SkillParametersPush> skill_params = get_parameters<SkillParametersPush>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("push",p);
    mp->create_strategy<FFStrategy>("wrench",1);
    Eigen::Matrix<double,6,1> TF_F_d;
    TF_F_d<<skill_params->F_push,0,0,0;
    std::cout << "F_push:  " << TF_F_d << std::endl;
    mp->get_strategy<FFStrategy>("wrench")->set_TF_F_ff(TF_F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    return mp;
}

bool Push::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersPush> skill_params = get_parameters<SkillParametersPush>();
    if(std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_skill).count()>=skill_params->duration*1000){
        return true;
    }
    bool reached_distance=true;
    for(unsigned i=0;i<3;i++){
        if((p.proprioception.T_T_EE(i,3)-m_TF_T_EE_0(i,3))*msrm_utils::sgn(skill_params->F_push(i))<skill_params->DX_max(i)){
            reached_distance=false;
        }
    }
    if(reached_distance){
        return true;
    }
    return false;
}

}
