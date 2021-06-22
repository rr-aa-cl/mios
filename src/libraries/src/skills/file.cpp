#include "mios/skills/file.hpp"
#include "mios/strategies/twist_wiggle_strategy.hpp"
#include "mios/strategies/twist_strategy.hpp"
#include "mios/strategies/ff_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"

namespace mios{
bool SkillParametersFile::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param(parameters,"f_contact",f_contact)){
        spdlog::error("Parameter f_contact could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"distance",distance)){
        spdlog::error("Parameter distance could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"file_amp",file_amp)){
        spdlog::error("Parameter file_amp could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"file_freq",file_freq)){
        spdlog::error("Parameter file_freq could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"t_contactless",t_contactless)){
        t_contactless=0;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersFile::get_parameter_list(){
    return {{"f_contact",{}},{"speed",{}},{"distance",{}},{"file_amp",{}},{"file_freq",{}},{"t_contactless",{}}};
}

File::File(const std::string& name, Memory* memory, Portal* portal):Skill("File",{"fileable"},name,memory,portal,{ControlMode::mCartTorque}),m_in_contact(false){

}

Eigen::Matrix<double,3,3> File::get_O_R_T_0(const Percept &p) const{
    if(get_object("fileable")->name!="NullObject"){
        return get_object("fileable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> File::get_initial_mp(const Percept& p){
    m_T_T_EE_0=p.proprioception.T_T_EE;
    std::shared_ptr<SkillParametersFile> skill_params = get_parameters<SkillParametersFile>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("file",p);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    Eigen::Matrix<double,6,1> K_x=m_memory->read_parameters()->control.cart_imp.K_x;
    Eigen::Matrix<double,6,1> xi_x=m_memory->read_parameters()->control.cart_imp.xi_x;
    K_x(2)=0;
    xi_x(2)=0;
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x,xi_x);
    mp->create_strategy<FFStrategy>("push",1);
    Eigen::Matrix<double,6,1> TF_F_ff;
    TF_F_ff<<0,0,skill_params->f_contact,0,0,0;
    mp->get_strategy<FFStrategy>("push")->set_TF_F_ff(TF_F_ff,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->create_strategy<TwistStrategy>("slide",1);
    Eigen::Matrix<double,6,1> TF_dX_d;
    TF_dX_d<<skill_params->speed,0,0,0,0,0;
    mp->get_strategy<TwistStrategy>("slide")->set_TF_dX_d(TF_dX_d,m_memory->read_parameters()->user.ddX_default);
    mp->create_strategy<TwistWiggleStrategy>("file",1);
    Eigen::Matrix<double,6,1> a_a,b_a,a_f,b_f,a_phi,b_phi;
    a_a.setZero();
    b_a.setZero();
    a_f.setZero();
    b_f.setZero();
    a_phi.setZero();
    b_phi.setZero();
    b_a<<0,skill_params->file_amp,0,0,0,0;
    b_f<<0,skill_params->file_freq,0,0,0,0;
    mp->get_strategy<TwistWiggleStrategy>("file")->set_coefficients(a_a,b_a,a_f,b_f,a_phi,b_phi);
    return mp;
}

bool File::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersFile> skill_params = get_parameters<SkillParametersFile>();
    if(fabs((p.proprioception.T_T_EE.block<2,1>(0,3)-m_T_T_EE_0.block<2,1>(0,3)).norm())>skill_params->distance){
        return true;
    }
    return false;
}

bool File::check_local_err_conditions(const Percept &p){
    std::shared_ptr<SkillParametersFile> skill_params = get_parameters<SkillParametersFile>();
    double f_contact = p.proprioception.TF_F_ext_K.block<3,1>(0,0).norm();
    if(f_contact>m_memory->read_parameters()->user.F_ext_contact(0)){
        m_in_contact=true;
    }else{
        m_in_contact=false;
        m_t_contact_loss=p.time;
    }

    if(!m_in_contact && std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_t_contact_loss).count()>skill_params->t_contactless){
        return true;
    }
    return false;
}

}
