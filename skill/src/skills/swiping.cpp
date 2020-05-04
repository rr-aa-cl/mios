#include "skills/swiping.hpp"
namespace mios{
swiping::swiping():Skill("swiping"){}
bool swiping::read_skill_parameters(const nlohmann::json& p){

    std::shared_ptr<ConfigSkill_swiping> c = std::static_pointer_cast<ConfigSkill_swiping>(this->_config);
    if(!msrm_utils::read_json_param<std::string>(p,"locations",c->locations)){
        c->locations.resize(0);
    }
    msrm_utils::read_json_param(p,"F_c",c->F_c);
    msrm_utils::read_json_param<double,2,1>(p,"speed",c->speed);
    msrm_utils::read_json_param<double,2,1>(p,"acc",c->acc);

    this->_n_p=c->locations.size();

    return true;
}
void swiping::build_primitives(const Percept& p){
    std::shared_ptr<ConfigSkill_swiping> c_skill = std::static_pointer_cast<ConfigSkill_swiping>(this->_config);
    for(unsigned i=0;i<c_skill->locations.size();i++){
        this->insert_mp<mp_basic>("move_"+std::to_string(i),p);
        std::shared_ptr<AttractorBasic> attr_move=std::static_pointer_cast<AttractorBasic>(this->get_mp("move_"+std::to_string(i))->get_attractor());
        std::shared_ptr<ConfigMP_mp_basic> c_move = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("move_"+std::to_string(i))->get_config());
        Object o;
        if(!this->_kb->load_object(c_skill->locations[i],o)){
            msrm_utils::print_warning("Could not load object" + o.name);
        }
        attr_move->attr_pose=this->_kb->transform_to_EE(o.TF_T_o(this->_config->frames.O_R_TF));
        attr_move->attr_fc(2)=c_skill->F_c;
        c_move->dX_d<<c_skill->speed(0)*c_skill->user.dX_max(0),c_skill->speed(1)*c_skill->user.dX_max(1);
        c_move->ddX_d<<c_skill->acc(0)*c_skill->user.ddX_max(0),c_skill->acc(1)*c_skill->user.ddX_max(1);
    }
    this->set_init_mp("move_0");

    c_skill->controller.K_0(2)=0;
    c_skill->controller.f_cntr_active(2)=1;
    c_skill->controller.f_cntr_k_p(2)=0.5;
    c_skill->controller.f_cntr_k_i(2)=0.1;
    c_skill->controller.f_cntr_d_max<<0.05,0.05,0.05;
    c_skill->controller.f_cntr_phi_max<<0.3;
    c_skill->controller.f_cntr_sf_on=true;
    c_skill->controller.TF_control=false;
}
std::tuple<bool,std::string> swiping::check_edges(const Percept& p){
    std::vector<std::string> mp_id = msrm_utils::split_string(this->_active_mp->get_id(),"_");
    if(std::stoi(mp_id[1])==this->_n_p){
        return std::tuple<bool,std::string>(false,"");
    }else{
        if(this->_active_mp->in_attractor(p)){
            return std::tuple<bool,std::string>(true,"move_"+std::to_string(std::stoi(mp_id[1])+1));
        }
    }

    return std::tuple<bool,std::string>(false,"");
}
bool swiping::check_local_suc_conditions(const Percept& p){
    std::vector<std::string> mp_id = msrm_utils::split_string(this->_active_mp->get_id(),"_");
    if(std::stoi(mp_id[1])==this->_n_p){
        if(this->_active_mp->in_attractor(p)){
            return true;
        }
    }
    return false;
}

bool swiping::check_local_err_conditions(const Percept &p){

    Eigen::Matrix<double,2,1> e;
    e<<p.TF_T_EE_d(0,3)-p.TF_T_EE(0,3),p.TF_T_EE_d(1,3)-p.TF_T_EE(1,3);
    double e_abs=msrm_utils::norm_2<2>(e);
    if(e_abs>this->_config->user.e_x_max(0)){
        msrm_utils::print_error("Deviation from desired trajectory during swiping was too large.");
        return true;
    }
    if(fabs(p.TF_F_ext(2))<this->_config->user.F_contact(2)){
        msrm_utils::print_error("I have lost contact while swiping.");
        return true;
    }
    return false;
}

void swiping::auxiliaries(const Percept &p){
}

void swiping::evaluate(){}
void swiping::create_config(){
    this->_config=std::make_shared<ConfigSkill_swiping>();
}
}
