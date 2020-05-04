#include "skills/insertion.hpp"

namespace mios {

insertion::insertion():Skill("insertion"){

}

bool insertion::read_skill_parameters(const nlohmann::json &p){
    std::shared_ptr<ConfigSkill_insertion> c = std::static_pointer_cast<ConfigSkill_insertion>(this->_config);
    msrm_utils::read_json_param<double,2,1>(p,"speed",c->speed);
    msrm_utils::read_json_param<double,1,1>(p,"F_contact",c->F_contact);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_a_r",c->wiggle_a_r);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_a_t",c->wiggle_a_t);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_a_z",c->wiggle_a_z);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_f_r",c->wiggle_f_r);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_f_t",c->wiggle_f_t);
    msrm_utils::read_json_param<double,1,1>(p,"wiggle_f_z",c->wiggle_f_z);
    msrm_utils::read_json_param<double,3,1>(p,"phi_init",c->phi_init);
    msrm_utils::read_json_param<double,3,1>(p,"offset_init",c->offset_init);
    return true;
}

Eigen::Matrix<double, 3, 3> insertion::get_O_R_TF(const Percept &p){
    return this->get_object_pose("hole",false).block<3,3>(0,0);
}

void insertion::build_primitives(const Percept &p){

    this->_cf1_sum_force=0;
    this->_cf1_cnt=0;

    this->insert_mp<mp_basic>("insert",p);
    this->set_init_mp("insert");

    std::shared_ptr<ConfigMP_mp_basic> c_insert = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("insert")->get_config());

    std::shared_ptr<ConfigSkill_insertion> c = std::static_pointer_cast<ConfigSkill_insertion>(this->_config);

    Eigen::Matrix<double,4,4> O_T_hole_est=this->get_object_pose("hole");
    this->TF_T_hole_est=O_T_hole_est;
    Eigen::Matrix<double,3,1> x_current=msrm_utils::invert_matrix(this->_config->frames.O_R_TF)*p.TF_T_EE.block<3,1>(0,3);
    Eigen::Matrix<double,3,1> dir = this->TF_T_hole_est.block<3,1>(0,3)-x_current;
    dir(2)=0;
    Eigen::Matrix<double,3,1> dir_n = dir/msrm_utils::norm_2<3>(dir);

    this->dir_hole=dir_n;

    c_insert->F_h_p=c->k_h_p;
    c_insert->F_h_d=c->k_h_d;

    c_insert->ff_fourier_b_a<<c->wiggle_a_t(0),c->wiggle_a_t(0),0,c->wiggle_a_r(0),c->wiggle_a_r(0),c->wiggle_a_z(0);
    c_insert->ff_fourier_b_f<<c->wiggle_f_t(0),c->wiggle_f_t(0)*3.0/4.0,0,c->wiggle_f_r(0),c->wiggle_f_r(0)*3.0/4.0,c->wiggle_f_z(0);
    c_insert->dX_d<<c->speed(0)*c->user.dX_max(0),c->speed(1)*c->user.dX_max(1);
    c_insert->ddX_d<<c->user.ddX_max(0),c->user.ddX_max(1);

    c_insert->D_x<<200,200,200,0,0,0;
    c_insert->dX_limit<<c->user.dX_max(0),c->user.dX_max(0),c->user.dX_max(0),
            c->user.dX_max(1),c->user.dX_max(1),c->user.dX_max(1);

    c_insert->F_stop<<0,0,c->F_contact,0,0,0;
    c_insert->DF_stop<<0,0,2,0,0,0;

    std::shared_ptr<AttractorBasic> attr_insert=std::static_pointer_cast<AttractorBasic>(this->get_mp("insert")->get_attractor());
    attr_insert->attr_pose=this->TF_T_hole_est;

    attr_insert->attr_ff<<0,0,c->controller.F_ff_0(2),0,0,0;
}

std::tuple<bool,std::string> insertion::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

bool insertion::check_local_suc_conditions(const Percept &p){
    bool depth = p.TF_T_EE(2,3)>this->TF_T_hole_est(2,3)-0.001;
    bool lateral = sqrt(pow(p.TF_T_EE(0,3)-TF_T_hole_est(0,3),2)+pow(p.TF_T_EE(1,3)-TF_T_hole_est(1,3),2))<0.002;
    return depth && lateral;
}

bool insertion::check_local_ex_conditions(const Percept &p){
    return true;
}

void insertion::create_config(){
    this->_config=std::make_shared<ConfigSkill_insertion>();
}

bool insertion::check_local_err_conditions(const Percept &p){
    double error_angle=acos(p.TF_T_EE.block<3,1>(0,2).dot(this->TF_T_hole_est.block<3,1>(0,2)));
    double dist_xy=sqrt(pow(p.TF_T_EE(0,3)-TF_T_hole_est(0,3),2)+pow(p.TF_T_EE(1,3)-TF_T_hole_est(1,3),2));
    double dist_z=fabs(p.TF_T_EE(2,3)-TF_T_hole_est(2,3));
    double radius,depth;
    if(!msrm_utils::read_json_param(this->get_object("hole").geometry,"radius",radius)){
        msrm_utils::print_error("Object "+this->get_object("hole").name+" has no geometry property <depth>.");
        return false;
    }
    if(!msrm_utils::read_json_param(this->get_object("hole").geometry,"depth",depth)){
        msrm_utils::print_error("Object "+this->get_object("hole").name+" has no geometry property <radius>.");
        return false;
    }
    if(dist_xy>radius || dist_z>depth*2 || error_angle>30.0/180.0*M_PI || p.TF_T_EE(2,3)<this->TF_T_hole_est(2,3)-depth-0.01){
        return true;
    }else{
        return false;
    }
}

void insertion::evaluate(){

        double c_err_1=this->_config->time_max+exp(msrm_utils::norm_2<3>(this->_eval.p_1.TF_T_EE.block<3,1>(0,3)-this->TF_T_hole_est.block<3,1>(0,3))*100)-1;
        double c_suc_1=this->_eval.p_1.time-this->_eval.p_0.time;

        double c_err_2=msrm_utils::norm_2<3>(this->_config->user.F_max.block<3,1>(0,0))+exp(msrm_utils::norm_2<3>(this->_eval.p_1.TF_T_EE.block<3,1>(0,3)-this->TF_T_hole_est.block<3,1>(0,3))*100)-1;
        double c_suc_2=0;
        if(this->_cf1_cnt==0){
            c_suc_2=this->_eval.cost_err;
        }else{
            c_suc_2=this->_cf1_sum_force/this->_cf1_cnt;
        }
        msrm_utils::print_critical_error("COST_ERR: " + std::to_string(c_err_1));
        msrm_utils::print_critical_error("COST_SUC: " + std::to_string(c_suc_1));
        this->_eval.cost_err=this->_config->w_cost_function[0]*c_err_1+this->_config->w_cost_function[1]*c_err_2;
        this->_eval.cost_suc=this->_config->w_cost_function[0]*c_suc_1+this->_config->w_cost_function[1]*c_suc_2;
}

void insertion::auxiliaries(const Percept &p){
    this->_cf1_sum_force+=msrm_utils::norm_2<3>(p.K_F_ext.block<3,1>(0,0));
    this->_cf1_cnt++;
}

}
