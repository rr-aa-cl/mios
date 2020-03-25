#include "skills/motions_generic_wiggle.hpp"

namespace mios {

motions_generic_wiggle::motions_generic_wiggle():Skill("motions_generic_wiggle"){

}

motions_generic_wiggle::~motions_generic_wiggle(){

}

bool motions_generic_wiggle::read_skill_parameters(const nlohmann::json &p){
    std::shared_ptr<ConfigSkill_motions_generic_wiggle> c = std::static_pointer_cast<ConfigSkill_motions_generic_wiggle>(this->_config);
    cpp_utils::read_json_param<double,6,1>(p,"dX_fourier_a_a",c->dX_fourier_a_a);
    cpp_utils::read_json_param<double,6,1>(p,"dX_fourier_b_a",c->dX_fourier_b_a);
    cpp_utils::read_json_param<double,6,1>(p,"dX_fourier_a_f",c->dX_fourier_a_f);
    cpp_utils::read_json_param<double,6,1>(p,"dX_fourier_b_f",c->dX_fourier_b_f);
    cpp_utils::read_json_param<double,6,1>(p,"dX_fourier_a_phi",c->dX_fourier_a_phi);
    cpp_utils::read_json_param<double,6,1>(p,"dX_fourier_b_phi",c->dX_fourier_b_phi);
    cpp_utils::read_json_param(p,"use_EE",c->use_EE);
    cpp_utils::read_json_param(p,"tap_to_finish",c->tap_to_finish);
    return true;
}

void motions_generic_wiggle::create_config(){
    this->_config=std::make_shared<ConfigSkill_motions_generic_wiggle>();
}

void motions_generic_wiggle::build_primitives(const Percept &p){

    this->insert_mp<mp_basic>("wiggle",p);
    this->set_init_mp("wiggle");

    std::shared_ptr<ConfigSkill_motions_generic_wiggle> c = std::static_pointer_cast<ConfigSkill_motions_generic_wiggle>(this->_config);
    std::shared_ptr<ConfigMP_mp_basic> c_wiggle = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("wiggle")->get_config());

    c_wiggle->dX_fourier_a_a=c->dX_fourier_a_a;
    c_wiggle->dX_fourier_b_a=c->dX_fourier_b_a;
    c_wiggle->dX_fourier_a_f=c->dX_fourier_a_f;
    c_wiggle->dX_fourier_b_f=c->dX_fourier_b_f;
    c_wiggle->dX_fourier_a_phi=c->dX_fourier_a_phi;
    c_wiggle->dX_fourier_b_phi=c->dX_fourier_b_phi;
}

Eigen::Matrix<double,3,3> motions_generic_wiggle::get_O_R_TF(const Percept &p){
    std::shared_ptr<ConfigSkill_motions_generic_wiggle> c = std::static_pointer_cast<ConfigSkill_motions_generic_wiggle>(this->_config);
    if(c->use_EE){
        return p.TF_T_EE.block<3,3>(0,0);
    }else{
        return Eigen::Matrix<double,3,3>::Zero();
    }
}

std::tuple<bool,std::string> motions_generic_wiggle::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

bool motions_generic_wiggle::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_motions_generic_wiggle> c = std::static_pointer_cast<ConfigSkill_motions_generic_wiggle>(this->_config);
    if(c->tap_to_finish){
        for(unsigned i=0;i<p.K_F_ext.rows();i++){
            if(fabs(p.K_F_ext(i))>this->_config->user.F_contact(i)){
                return true;
            }
        }
    }
    return false;
}

bool motions_generic_wiggle::check_local_ex_conditions(const Percept &p){
    return true;
}

void motions_generic_wiggle::evaluate(){
    this->_eval.cost_err=0;
    this->_eval.cost_suc=0;
}

}
