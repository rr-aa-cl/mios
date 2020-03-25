#include "skills/rehab.hpp"

namespace mios{

rehab::rehab():Skill("rehab"){

}
rehab::~rehab(){

}

bool rehab::read_skill_parameters(const nlohmann::json& p){

    cpp_utils::read_json_param(p["a_z"],static_cast<ConfigSkill_rehab*>(this->_config)->a_z);
    cpp_utils::read_json_param(p["a_y"],static_cast<ConfigSkill_rehab*>(this->_config)->a_y);
    cpp_utils::read_json_param(p["a_x"],static_cast<ConfigSkill_rehab*>(this->_config)->a_x);
    cpp_utils::read_json_param(p["a_r"],static_cast<ConfigSkill_rehab*>(this->_config)->a_r);

    cpp_utils::read_json_param(p["f_z"],static_cast<ConfigSkill_rehab*>(this->_config)->f_z);
    cpp_utils::read_json_param(p["f_y"],static_cast<ConfigSkill_rehab*>(this->_config)->f_y);
    cpp_utils::read_json_param(p["f_x"],static_cast<ConfigSkill_rehab*>(this->_config)->f_x);
    cpp_utils::read_json_param(p["f_r"],static_cast<ConfigSkill_rehab*>(this->_config)->f_r);

    cpp_utils::read_json_param(p["phi_x"],static_cast<ConfigSkill_rehab*>(this->_config)->phi_x);
    cpp_utils::read_json_param(p["phi_y"],static_cast<ConfigSkill_rehab*>(this->_config)->phi_y);

    cpp_utils::read_json_param(p["stiffness"],static_cast<ConfigSkill_rehab*>(this->_config)->stiffness);
    cpp_utils::read_json_param(p["speed"],static_cast<ConfigSkill_rehab*>(this->_config)->speed);

    cpp_utils::read_json_param(p["motion"],static_cast<ConfigSkill_rehab*>(this->_config)->motion);

    return true;


}

void rehab::build_primitives(const Percept& p){


    ConfigSkill_rehab* c_skill=static_cast<ConfigSkill_rehab*>(this->_config);

    //Adapt the speed of the circular motion
    //    if(c_skill->motion == "circle") {

    //        this->insert_mp("rehab",new mp_basic(),p);
    //        this->set_init_mp("rehab");

    //        ConfigMP_mp_basic* c_rehab = static_cast<ConfigMP_mp_basic*>(this->get_mp("rehab")->get_config());

    //        std::cout << c_skill->motion << std::endl;

    //        c_rehab->dX_fourier_a_a<<c_skill->a_x,c_skill->a_y,c_skill->a_z,c_skill->a_r, c_skill->a_r, 0;
    //        c_rehab->dX_fourier_a_f<<c_skill->f_x *c_skill->speed,c_skill->f_y*c_skill->speed,c_skill->f_z,0,0,0.0;
    //        c_rehab->dX_fourier_a_phi<<c_skill->phi_x,c_skill->phi_y,0,0,0,0;
    //        this->_config->controller.K_0(0) = c_skill->stiffness;
    //        this->_config->controller.K_0(1) = c_skill->stiffness;

    //    }


    //    else if(c_skill->motion == "horizontalLine") {

    this->insert_mp("rehab",new mp_basic(),p);
    this->set_init_mp("rehab");

    ConfigMP_mp_basic* c_rehab = static_cast<ConfigMP_mp_basic*>(this->get_mp("rehab")->get_config());

    Eigen::Matrix<double,4,4> start_pose;
    Eigen::Matrix<double,4,4> end_pose;

    start_pose = this->get_object_pose("start_pose");
    end_pose = this->get_object_pose("end_pose");



    Eigen::VectorXd r_start, r_end; r_start = Eigen::VectorXd::Zero(3);   r_end = Eigen::VectorXd::Zero(3);

    Eigen::VectorXd r_between; r_between = Eigen::VectorXd::Zero(3);
    Eigen::VectorXd r_betweenNorm; r_betweenNorm = Eigen::VectorXd::Zero(3);

    Eigen::VectorXd r_y; r_y = Eigen::VectorXd::Zero(3);
    r_y << 0, 1, 0;
    r_start = start_pose.block(0,3,3,1);
    r_end = end_pose.block(0,3,3,1);

    r_between =  r_start -  r_end;
    r_betweenNorm = r_between / (std::sqrt(r_between.transpose() * r_between));
    double angle;
    if(r_between(2) > 0.0) {

        angle = -std::acos ( r_y.dot(r_betweenNorm) );
    }
    else {
        angle = std::acos ( r_y.dot(r_betweenNorm) );
    }
    std::cout<<  "angle"   << angle*180/M_PI << std::endl;
    std::cout << "r_betweenNorm"  << r_betweenNorm << std::endl;
    std::cout << "r_between"  << r_between << std::endl;

    std::cout << "r_axis"  << r_y.dot(r_between) << std::endl;



    double amplitude = std::sqrt(r_between.transpose() * r_between);
    std::cout << "angle"  << angle << std::endl;


    //angle/M_PI*180
    this->_config->frames.O_R_TF = this->_config->frames.O_R_TF * cpp_utils::eulerRPY_to_mat(angle*180/M_PI,0.0 ,0.0);


    //  c_rehab->dX_fourier_a_a<<0.0,c_skill->a_y,c_skill->a_z,c_skill->a_r, c_skill->a_r, 0;
    c_rehab->dX_fourier_a_a<<0.0,0.5*amplitude,c_skill->a_z,c_skill->a_r, c_skill->a_r, 0;

    c_rehab->dX_fourier_a_f<<c_skill->f_x *c_skill->speed,c_skill->f_y*c_skill->speed,c_skill->f_z,0,0,0.0;
    c_rehab->dX_fourier_a_phi<<c_skill->phi_x,c_skill->phi_y,0,0,0,0;
    this->_config->controller.K_0(0) = c_skill->stiffness;
    this->_config->controller.K_0(1) = c_skill->stiffness;

    //    }

    //Adapt the stiffness of the Impedance controller according to the desired support


    //  Eigen::VectorXd r_teach; r_teach = Eigen::VectorXd::Zero(4);
    // Eigen::VectorXd theta_teach; theta_teach = Eigen::VectorXd::Zero(4);

    //   r_teach << 1.0, 1.2, 0.7, 1.1;
    //  theta_teach << M_PI/4, M_PI/2, M_PI, 3*M_PI/2;


    //c_rehab->r_teach = r_teach;



    //c_rehab->theta_teach = theta_teach;

}

std::tuple<bool,std::string> rehab::check_edges(const Percept& p){return std::tuple<bool,std::string>(false,"");}

bool rehab::check_local_suc_conditions(const Percept& p){



    return false;
}

void rehab::evaluate(){}

void rehab::create_config(){

    this->_config=new ConfigSkill_rehab();
}
}
