#include "skills/hand_guiding.hpp"


namespace mios{

bool SkillParametersHandGuiding::read_parameters(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"fix_dim",fix_dim)){
        fix_dim.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"use_walls",use_walls)){
        use_walls.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"dist_walls",dist_walls)){
        dist_walls<<-1000,1000,-1000,1000,-1000,1000;
    }
    return true;
}

HandGuiding::HandGuiding(const std::string &id, Memory *memory, const Percept &p):Skill("HandGuiding",{},id,memory,p){
}

std::shared_ptr<ManipulationPrimitive> HandGuiding::get_initial_mp(const Percept &p_0){
    std::shared_ptr<BasicPrimitive> mp = create_mp<BasicPrimitive,MPParametersBasic,BasicAttractor>("guiding",p_0);
    std::shared_ptr<SkillParametersHandGuiding> skill_params = get_parameters<SkillParametersHandGuiding>();
    std::shared_ptr<MPParametersBasic> mp_params = get_active_mp()->get_parameters<MPParametersBasic>();

    m_memory->get_parameters()->control.virtual_cube.active=true;
    m_memory->get_parameters()->control.virtual_cube.damping<<0.004;
    m_memory->get_parameters()->control.virtual_cube.damping_dist<<0.03;
    m_memory->get_parameters()->control.virtual_cube.eta<<0.001;
    m_memory->get_parameters()->control.virtual_cube.rho_min<<0.02;

    for(unsigned i=0;i<skill_params->fix_dim.rows();i++){
        if(i<3){
            if(skill_params->fix_dim(i)==1){
                m_memory->get_parameters()->control.cart_imp.K_x(i)=1500;
                m_memory->get_parameters()->control.cart_imp.xi(i)=0.7;
            }else{
                m_memory->get_parameters()->control.cart_imp.K_x(i)=0;
                m_memory->get_parameters()->control.cart_imp.xi(i)=0;
            }
        }else{
            if(skill_params->fix_dim(i)==1){
                m_memory->get_parameters()->control.cart_imp.K_x(i)=150;
                m_memory->get_parameters()->control.cart_imp.xi(i)=1.5;
            }else{
                m_memory->get_parameters()->control.cart_imp.K_x(i)=0;
                m_memory->get_parameters()->control.cart_imp.xi(i)=0;
            }
        }
    }

    for(unsigned i=0;i<skill_params->dist_walls.rows();i++){
        m_memory->get_parameters()->control.virtual_cube.walls(i)=skill_params->dist_walls(i);
    }

    for(unsigned i=0;i<skill_params->use_walls.rows();i++){
        if(skill_params->use_walls(i)==0){
            m_memory->get_parameters()->control.virtual_cube.walls(i)=1000;
            if(i%2==0){
                m_memory->get_parameters()->control.virtual_cube.walls(i)*=-1;
            }
        }
    }
    return mp;
}

bool HandGuiding::check_local_suc_conditions(const Percept& p){
    return false;
}

}
