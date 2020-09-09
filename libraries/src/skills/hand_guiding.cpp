#include "skills/hand_guiding.hpp"
#include "strategies/cart_compliance_strategy.hpp"


namespace mios{

bool SkillParametersHandGuiding::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"fix_dim",fix_dim)){
        fix_dim.setZero();
    }
    if(!msrm_utils::read_json_param(parameters,"use_walls",use_walls)){
        use_walls=false;
    }
    if(use_walls && !msrm_utils::read_json_param<double,6,1>(parameters,"dist_walls",dist_walls)){
        spdlog::error("Parameter dist_walls could not be loaded but is mandatory when walls are used.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersHandGuiding::get_parameter_list(){
    return {{"fix_dim",{}},{"use_walls",{}},{"dist_walls",{}}};
}

HandGuiding::HandGuiding(const std::string &id, Memory *memory, Portal* portal):Skill("HandGuiding",{},id,memory,portal,{ControlMode::mCartTorque}){
    std::shared_ptr<SkillParametersHandGuiding> skill_params = get_parameters<SkillParametersHandGuiding>();
    m_memory->get_parameters()->safety.virtual_cube.active=skill_params->use_walls;
    m_memory->get_parameters()->safety.virtual_cube.damping=0.004;
    m_memory->get_parameters()->safety.virtual_cube.damping_dist=0.03;
    m_memory->get_parameters()->safety.virtual_cube.eta=0.001;
    m_memory->get_parameters()->safety.virtual_cube.rho_min=0.02;
    m_memory->get_parameters()->safety.virtual_cube.walls=skill_params->dist_walls;
    m_memory->get_parameters()->safety.virtual_cube.f_max=30;
}

std::shared_ptr<ManipulationPrimitive> HandGuiding::get_initial_mp(const Percept &p_0){
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("guiding",p_0);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    std::shared_ptr<SkillParametersHandGuiding> skill_params = get_parameters<SkillParametersHandGuiding>();

    for(unsigned i=0;i<skill_params->fix_dim.rows();i++){
        if(i<3){
            if(skill_params->fix_dim(i)==1){
                m_memory->get_parameters()->control.cart_imp.K_x(i)=1500;
                m_memory->get_parameters()->control.cart_imp.xi_x(i)=0.7;
            }else{
                m_memory->get_parameters()->control.cart_imp.K_x(i)=0;
                m_memory->get_parameters()->control.cart_imp.xi_x(i)=0;
            }
        }else{
            if(skill_params->fix_dim(i)==1){
                m_memory->get_parameters()->control.cart_imp.K_x(i)=150;
                m_memory->get_parameters()->control.cart_imp.xi_x(i)=1.5;
            }else{
                m_memory->get_parameters()->control.cart_imp.K_x(i)=0;
                m_memory->get_parameters()->control.cart_imp.xi_x(i)=0;
            }
        }
    }
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(m_memory->read_parameters()->control.cart_imp.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);

    //    for(unsigned i=0;i<skill_params->dist_walls.rows();i++){
    //        m_memory->get_parameters()->safety.virtual_cube.walls(i)=skill_params->dist_walls(i);
    //    }

    //    for(unsigned i=0;i<skill_params->use_walls.rows();i++){
    //        if(skill_params->use_walls(i)==0){
    //            m_memory->get_parameters()->safety.virtual_cube.walls(i)=1000;
    //            if(i%2==0){
    //                m_memory->get_parameters()->safety.virtual_cube.walls(i)*=-1;
    //            }
    //        }
    //    }
    return mp;
}

bool HandGuiding::check_local_suc_conditions(const Percept& p){
    return false;
}

}
