#include "skills/extraction.hpp"

namespace mios {

extraction::extraction():Skill("extraction"){
}

void extraction::create_config(){
    this->_config = std::make_shared<ConfigSkill_extraction>();
}

bool extraction::read_skill_parameters(const nlohmann::json &p){
    std::shared_ptr<ConfigSkill_extraction> c = std::static_pointer_cast<ConfigSkill_extraction>(this->_config);
    msrm_utils::read_json_param<double,2,1>(p,"speed",c->speed);
    msrm_utils::read_json_param<double,1,1>(p,"F_contact",c->F_contact);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_a_r",c->wiggle_a_r);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_a_t",c->wiggle_a_t);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_a_z",c->wiggle_a_z);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_f_r",c->wiggle_f_r);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_f_t",c->wiggle_f_t);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_f_z",c->wiggle_f_z);
    return true;
}

void extraction::build_primitives(const Percept &p){

    this->insert_mp<mp_basic>("extract",p);
    this->set_init_mp("extract");

    std::shared_ptr<ConfigMP_mp_basic> c_extract = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("extract")->get_config());

    std::shared_ptr<ConfigSkill_extraction> c = std::static_pointer_cast<ConfigSkill_extraction>(this->_config);

    this->TF_T_hole_est=this->get_object_pose("hole");

    c_extract->D_x<<200,200,200,10,10,10;
    c_extract->dX_limit<<c->user.dX_max(0),c->user.dX_max(0),c->user.dX_max(0),
            c->user.dX_max(1),c->user.dX_max(1),c->user.dX_max(1);

    c_extract->ff_fourier_b_a<<c->wiggle_a_t(0),c->wiggle_a_t(0),0,c->wiggle_a_r(0),c->wiggle_a_r(0),c->wiggle_a_z(0);
    c_extract->ff_fourier_b_f<<c->wiggle_f_t(0),c->wiggle_f_t(0)*3.0/4.0,0,c->wiggle_f_r(0),c->wiggle_f_r(0)*3.0/4.0,c->wiggle_f_z(0);
    c_extract->dX_d<<c->speed(0)*c->user.dX_max(0),c->speed(1)*c->user.dX_max(1);
    c_extract->ddX_d<<c->user.ddX_max(0),c->user.ddX_max(1);

    std::shared_ptr<AttractorBasic> attr_extract=std::static_pointer_cast<AttractorBasic>(this->get_mp("extract")->get_attractor());
    attr_extract->attr_vel<<0,0,-c->user.dX_max[0]*c->speed[0],0,0,0;

    c_extract->F_stop<<0,0,c->F_contact,0,0,0;
    c_extract->DF_stop<<0,0,2,0,0,0;
}

Eigen::Matrix<double,3,3> extraction::get_O_R_TF(const Percept& p){
    Eigen::Matrix<double,3,3> R = msrm_utils::eulerRPY_to_mat(0,180,0);
    Eigen::Matrix<double,3,3> R_o = this->get_object_pose("hole",false).block<3,3>(0,0);
//    return rotate_matrix(R_o,R);
    return this->get_object_pose("hole",false).block<3,3>(0,0);
}

std::tuple<bool,std::string> extraction::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

bool extraction::check_local_suc_conditions(const Percept &p){
    double depth;
    if(!msrm_utils::read_json_param(this->get_object("hole").geometry,"depth",depth)){
        msrm_utils::print_error("Object "+this->get_object("hole").name+" has no geometry property <depth>.");
        return false;
    }
    return p.TF_T_EE(2,3)<this->TF_T_hole_est(2,3)-depth-0.01;
}

bool extraction::check_local_ex_conditions(const Percept &p){
    return true;
}

bool extraction::check_local_err_conditions(const Percept &p){
    return false;
}

void extraction::evaluate(){
    this->_eval.cost_err=this->_eval.p_1.time-this->_eval.p_0.time;
    this->_eval.cost_suc=0;
}

}

