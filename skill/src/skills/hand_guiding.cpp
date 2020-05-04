#include "skills/hand_guiding.hpp"


namespace mios{

hand_guiding::hand_guiding():Skill("hand_guiding"){}

bool hand_guiding::read_skill_parameters(const nlohmann::json& p){
    std::shared_ptr<ConfigSkill_hand_guiding> c = std::static_pointer_cast<ConfigSkill_hand_guiding>(this->_config);
    if(!msrm_utils::read_json_param<double,6,1>(p,"fix_dim",c->fix_dim)){
        c->fix_dim.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(p,"use_walls",c->use_walls)){
        c->use_walls.setZero();
    }
    if(!msrm_utils::read_json_param<double,6,1>(p,"dist_walls",c->dist_walls)){
        c->dist_walls<<-1000,1000,-1000,1000,-1000,1000;
    }
    return true;
}

void hand_guiding::build_primitives(const Percept& p){
    this->insert_mp<mp_basic>("guiding",p);
    this->set_init_mp("guiding");

    std::shared_ptr<ConfigSkill_hand_guiding> c = std::static_pointer_cast<ConfigSkill_hand_guiding>(this->_config);
    std::shared_ptr<ConfigMP_mp_basic> c_guiding = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("guiding")->get_config());

    this->_config->controller.virt_cube_on=true;
    this->_config->controller.virt_cube_damp<<0.004;
    this->_config->controller.virt_cube_damp_dist<<0.03;
    this->_config->controller.virt_cube_eta<<0.001;
    this->_config->controller.virt_cube_rho_min<<0.02;

    for(unsigned i=0;i<c->fix_dim.rows();i++){
        if(i<3){
            if(c->fix_dim(i)==1){
                this->_config->controller.K_0(i)=1500;
                this->_config->controller.xi(i)=0.7;
            }else{
                this->_config->controller.K_0(i)=0;
                this->_config->controller.xi(i)=0;
            }
        }else{
            if(c->fix_dim(i)==1){
                this->_config->controller.K_0(i)=150;
                this->_config->controller.xi(i)=1.5;
            }else{
                this->_config->controller.K_0(i)=0;
                this->_config->controller.xi(i)=0;
            }
        }
    }

    for(unsigned i=0;i<c->dist_walls.rows();i++){
        this->_config->controller.virt_cube_walls(i)=c->dist_walls(i);
    }

    for(unsigned i=0;i<c->use_walls.rows();i++){
        if(c->use_walls(i)==0){
            this->_config->controller.virt_cube_walls(i)=1000;
            if(i%2==0){
                this->_config->controller.virt_cube_walls(i)*=-1;
            }
        }
    }
}

std::tuple<bool,std::string> hand_guiding::check_edges(const Percept& p){
    return std::tuple<bool,std::string>(false,"");
}
bool hand_guiding::check_local_suc_conditions(const Percept& p){
    return false;
}
void hand_guiding::evaluate(){

}
void hand_guiding::create_config(){
    this->_config=std::make_shared<ConfigSkill_hand_guiding>();
}
}
