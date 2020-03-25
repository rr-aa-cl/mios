#include "skills/look_at.hpp"

namespace mios {

look_at::look_at():Skill("look_at"){

}

look_at::~look_at(){

}

bool look_at::read_skill_parameters(const Json::Value &p){

    cpp_utils::read_json_param(p["speed"],static_cast<Config_look_at*>(this->_config)->speed);
    cpp_utils::read_json_param(p["acc"],static_cast<Config_look_at*>(this->_config)->acc);
    cpp_utils::read_json_param(p["hover_a"],static_cast<Config_look_at*>(this->_config)->hover_a);
    cpp_utils::read_json_param(p["hover_f"],static_cast<Config_look_at*>(this->_config)->hover_f);
    cpp_utils::read_json_param(p["wink_a"],static_cast<Config_look_at*>(this->_config)->wink_a);
    cpp_utils::read_json_param(p["wink_f"],static_cast<Config_look_at*>(this->_config)->wink_f);
    cpp_utils::read_json_param(p["t_hover"],static_cast<Config_look_at*>(this->_config)->t_hover);
    cpp_utils::read_json_param(p["r_poses"],static_cast<Config_look_at*>(this->_config)->r_poses);
    cpp_utils::read_json_param(p["F_confirm"],static_cast<Config_look_at*>(this->_config)->F_confirm);
    return true;
}

void look_at::create_config(){
    this->_config=new Config_look_at();
}

void look_at::build_primitives(const Percept &p){
    this->cnt_color=1;
    this->color=10;
    this->insert_mp("move",new mp_basic(),p,&this->_config->config_global);
    this->insert_mp("look",new mp_basic(),p,&this->_config->config_global);
    this->insert_mp("adjust",new mp_basic(),p,&this->_config->config_global);
    this->insert_mp("wink",new mp_basic(),p,&this->_config->config_global);
    this->set_init_mp("move");

    Config_look_at* c_skill=static_cast<Config_look_at*>(this->_config);

    // move to look pose
    ConfigMP_mp_basic* c_move = static_cast<ConfigMP_mp_basic*>(this->get_mp("move")->get_config());
    c_move->dX_d<<c_skill->speed*c_skill->config_global.dX_max(0),c_skill->speed*c_skill->config_global.dX_max(1);
    c_move->ddX_d<<c_skill->acc*c_skill->config_global.ddX_max(0),c_skill->acc*c_skill->config_global.ddX_max(1);
    AttractorBasic* attr_move=static_cast<AttractorBasic*>(this->get_mp("move")->get_attractor());
    attr_move->attr_vel<<0,0,0,0,0,0;
    attr_move->attr_pose=this->get_object_pose("look_from");

    // hover
    Eigen::Matrix<double,3,1> O_z;
    O_z<<0,0,1;
    Eigen::Matrix<double,3,1> TF_z=cpp_utils::rotate_vector(O_z,cpp_utils::invert_matrix(this->_config->config_global.O_R_TF));
    ConfigMP_mp_basic* c_look = static_cast<ConfigMP_mp_basic*>(this->get_mp("look")->get_config());
    c_look->dX_fourier_b_a<<TF_z(0)*c_skill->hover_a,TF_z(1)*c_skill->hover_a,TF_z(2)*c_skill->hover_a,0,0,0;
    c_look->dX_fourier_b_f<<0,c_skill->hover_f,0,0,0,0;

    // wink
    ConfigMP_mp_basic* c_wink = static_cast<ConfigMP_mp_basic*>(this->get_mp("wink")->get_config());
    c_wink->dX_fourier_b_a<<0,0,0,0,0,c_skill->wink_a;
    c_wink->dX_fourier_b_f<<0,0,0,0,0,c_skill->wink_f;

    // adjust
    ConfigMP_mp_basic* c_adjust = static_cast<ConfigMP_mp_basic*>(this->get_mp("adjust")->get_config());
    c_adjust->dX_d<<c_skill->speed*c_skill->config_global.dX_max(0),c_skill->speed*c_skill->config_global.dX_max(1);
    c_adjust->ddX_d<<c_skill->acc*c_skill->config_global.ddX_max(0),c_skill->acc*c_skill->config_global.ddX_max(1);
}

std::tuple<bool,std::string> look_at::check_edges(const Percept &p){
    Config_look_at* c_skill=static_cast<Config_look_at*>(this->_config);
    int selector=rand()%3;
    if(this->_active_mp->get_id()=="move"){
        if(this->_active_mp->in_attractor(p)){
            switch(selector){
            case 0:{
                AttractorBasic* attr_adjust=static_cast<AttractorBasic*>(this->get_mp("adjust")->get_attractor());
                Eigen::Matrix<double,3,1> x_shift;
                x_shift<<cpp_utils::fRand(-c_skill->r_poses,c_skill->r_poses),cpp_utils::fRand(-c_skill->r_poses,c_skill->r_poses),0;
                attr_adjust->attr_pose=this->get_object_pose("look_from");
                attr_adjust->attr_pose(0,3)+=x_shift(0);
                attr_adjust->attr_pose(1,3)+=x_shift(1);
                attr_adjust->attr_pose(2,3)+=x_shift(2);
                return std::tuple<bool,std::string>(true,"adjust");break;
            }
            case 1: this->_t_look_start=this->_active_mp->get_time();
                return std::tuple<bool,std::string>(true,"look");break;
            case 2: this->_t_wink_start=this->_active_mp->get_time();
                return std::tuple<bool,std::string>(true,"wink");break;
            default:break;
            }
        }
    }
    if(this->_active_mp->get_id()=="adjust"){
        if(this->_active_mp->in_attractor(p)){
            switch(selector){
            //            case 0:{
            //                AttractorBasic* attr_adjust=static_cast<AttractorBasic*>(this->get_mp("adjust")->get_attractor());
            //                Eigen::Matrix<double,3,1> x_shift;
            //                x_shift<<fRand(-c_skill->r_poses,c_skill->r_poses),fRand(-c_skill->r_poses,c_skill->r_poses),0;
            //                attr_adjust->attr_pose=this->get_object_pose("look_from");
            //                attr_adjust->attr_pose(0,3)+=x_shift(0);
            //                attr_adjust->attr_pose(1,3)+=x_shift(1);
            //                attr_adjust->attr_pose(2,3)+=x_shift(2);
            //                return std::tuple<bool,std::string>(true,"adjust");break;
            //            }
            case 1: this->_t_look_start=this->_active_mp->get_time();
                return std::tuple<bool,std::string>(true,"look");break;
            case 2: this->_t_wink_start=this->_active_mp->get_time();
                return std::tuple<bool,std::string>(true,"wink");break;
            default:break;
            }
        }
    }
    if(this->_active_mp->get_id()=="look"){
        if(p.time-this->_t_look_start>c_skill->t_hover){
            switch(selector){
            case 0:{
                AttractorBasic* attr_adjust=static_cast<AttractorBasic*>(this->get_mp("adjust")->get_attractor());
                Eigen::Matrix<double,3,1> x_shift;
                x_shift<<cpp_utils::fRand(-c_skill->r_poses,c_skill->r_poses),cpp_utils::fRand(-c_skill->r_poses,c_skill->r_poses),0;
                attr_adjust->attr_pose=this->get_object_pose("look_from");
                attr_adjust->attr_pose(0,3)+=x_shift(0);
                attr_adjust->attr_pose(1,3)+=x_shift(1);
                attr_adjust->attr_pose(2,3)+=x_shift(2);
                return std::tuple<bool,std::string>(true,"adjust");break;
            }
                //            case 1: this->_t_look_start=this->_active_mp->get_time();
                //                return std::tuple<bool,std::string>(true,"look");break;
            case 2: this->_t_wink_start=this->_active_mp->get_time();
                return std::tuple<bool,std::string>(true,"wink");break;
            default:break;
            }
        }
    }
    if(this->_active_mp->get_id()=="wink"){
        if(p.time-this->_t_wink_start>1/(c_skill->wink_f*4)){
            switch(selector){
            case 0:{
                AttractorBasic* attr_adjust=static_cast<AttractorBasic*>(this->get_mp("adjust")->get_attractor());
                Eigen::Matrix<double,3,1> x_shift;
                x_shift<<cpp_utils::fRand(-c_skill->r_poses,c_skill->r_poses),cpp_utils::fRand(-c_skill->r_poses,c_skill->r_poses),0;
                attr_adjust->attr_pose=this->get_object_pose("look_from");
                attr_adjust->attr_pose(0,3)+=x_shift(0);
                attr_adjust->attr_pose(1,3)+=x_shift(1);
                attr_adjust->attr_pose(2,3)+=x_shift(2);
                return std::tuple<bool,std::string>(true,"adjust");break;
            }
            case 1: this->_t_look_start=this->_active_mp->get_time();
                return std::tuple<bool,std::string>(true,"look");break;
                //            case 2: this->_t_wink_start=this->_active_mp->get_time();
                //                return std::tuple<bool,std::string>(true,"wink");break;
                //            }
            default:break;
            }
        }
    }
    //    if(this->_active_mp->get_id()=="wink"){
    //        if(p.time-this->_eval.percepts["move"].time>10){
    //            return std::tuple<bool,std::string>(false,"");
    //        }
    //    }
    return std::tuple<bool,std::string>(false,"");
}

Eigen::Matrix<double,3,3> look_at::get_O_R_TF(const Percept &p){
    Eigen::Matrix<double,3,1> x_at = this->get_object_pose("look_at",false).block<3,1>(0,3);
    Eigen::Matrix<double,3,1> x_from = this->get_object_pose("look_from",false).block<3,1>(0,3);

    Eigen::Matrix<double,3,1> O_z;
    O_z<<0,0,1;
    Eigen::Matrix<double,3,1> TF_z=(x_at-x_from)/cpp_utils::norm_2<3>(x_at-x_from);

    Eigen::Matrix<double,3,1> TF_y = O_z.cross(TF_z);
    TF_y=TF_y/cpp_utils::norm_2<3>(TF_y);
    Eigen::Matrix<double,3,1> TF_x = -TF_z.cross(TF_y);
    TF_x=TF_x/cpp_utils::norm_2<3>(TF_x);
    Eigen::Matrix<double,3,3> O_R_TF;
    O_R_TF<<TF_x,TF_y,TF_z;
    //    return O_R_TF;
    return this->get_object_pose("look_from",false).block<3,3>(0,0);
}


bool look_at::check_local_suc_conditions(const Percept &p){
    Config_look_at* c_skill=static_cast<Config_look_at*>(this->_config);
    for(unsigned i=0;i<3;i++){
        if(p.TF_F_ext(i)>c_skill->F_confirm){
            return true;
        }
    }
    return false;
}

bool look_at::check_local_ex_conditions(const Percept &p){
    return true;
}

bool look_at::check_local_err_conditions(const Percept &p){
    return false;
}

void look_at::evaluate(){
    this->_eval.cost_err=0;
    this->_eval.cost_suc=0;
}

}
