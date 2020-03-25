#include "skills/move_cart_relative.hpp"

namespace mios {

move_cart_relative::move_cart_relative():Skill("move_cart_relative"){
}

move_cart_relative::~move_cart_relative(){

}

bool move_cart_relative::read_skill_parameters(const Json::Value &p){

    cpp_utils::read_json_param(p["speed"],static_cast<Config_move_cart_relative*>(this->_config)->speed);
    cpp_utils::read_json_param(p["acc"],static_cast<Config_move_cart_relative*>(this->_config)->acc);
    cpp_utils::read_json_param(p["EE"],static_cast<Config_move_cart_relative*>(this->_config)->EE);
    cpp_utils::read_json_param<double,6,1>(p["DX"],static_cast<Config_move_cart_relative*>(this->_config)->DX);
    return true;
}

void move_cart_relative::create_config(){
    this->_config=new Config_move_cart_relative();
}

void move_cart_relative::build_primitives(const Percept &p){
    this->insert_mp("move_cart_relative",new mp_basic(),p,&this->_config->config_global);
    this->set_init_mp("move_cart_relative");

    ConfigMP_mp_basic* c_move_cart_relative = static_cast<ConfigMP_mp_basic*>(this->get_mp("move_cart_relative")->get_config());

    Config_move_cart_relative* c_skill=static_cast<Config_move_cart_relative*>(this->_config);

    c_move_cart_relative->dX_d<<c_skill->speed*c_skill->config_global.dX_max(0),c_skill->speed*c_skill->config_global.dX_max(1);
    c_move_cart_relative->ddX_d<<c_skill->acc*c_skill->config_global.ddX_max(0),c_skill->acc*c_skill->config_global.ddX_max(1);

    AttractorBasic* attr_move_cart_relative=static_cast<AttractorBasic*>(this->get_mp("move_cart_relative")->get_attractor());

    attr_move_cart_relative->attr_vel<<0,0,0,0,0,0;
    attr_move_cart_relative->attr_pose=cpp_utils::rotate_matrix(p.O_T_EE,cpp_utils::invert_matrix(this->get_config()->config_global.O_R_TF));
    Eigen::Matrix<double,3,1> DX;
    Eigen::Matrix<double,3,1> TF_DX;
    DX<<c_skill->DX(0),c_skill->DX(1),c_skill->DX(2);
    if(c_skill->EE){
        TF_DX=cpp_utils::rotate_vector(DX,this->get_config()->config_global.O_R_TF);
    }else{
        TF_DX=DX;
    }
    attr_move_cart_relative->attr_pose(0,3)+=TF_DX(0);
    attr_move_cart_relative->attr_pose(1,3)+=TF_DX(1);
    attr_move_cart_relative->attr_pose(2,3)+=TF_DX(2);
    std::cout<<"TF_T_EE_g: "<<attr_move_cart_relative->attr_pose<<std::endl;
    Eigen::Matrix<double,3,3> R_tmp=cpp_utils::eulerRPY_to_mat(c_skill->DX(3),c_skill->DX(4),c_skill->DX(5));
//    attr_move_cart_relative->attr_pose=rotate_matrix(attr_move_cart_relative->attr_pose,R_tmp);
}

std::tuple<bool,std::string> move_cart_relative::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"move_cart_relative");
}

bool move_cart_relative::check_local_suc_conditions(const Percept &p){
    return this->get_mp("move_cart_relative")->in_attractor(p);
}

bool move_cart_relative::check_local_ex_conditions(const Percept &p){
    return true;
}

void move_cart_relative::evaluate(){
    this->_eval.cost_err=this->_eval.p_1.time-this->_eval.p_0.time;
    this->_eval.cost_suc=0;
}

//SoundCmd move_cart_relative::cycle_sound(const Percept &p){
//    return SoundCmd("franka_gesture_1.mp3",true,1);
//}

//LEDCmd move_cart_relative::cycle_led(const Percept &p){
//    LEDCmd led_cmd(10);
//    switch(this->led_selector){
//    case 1: led_cmd.led["far-left"].colors=std::make_tuple<unsigned,unsigned,unsigned>(255,0,0);break;
//    case 2: led_cmd.led["left"].colors=std::make_tuple<unsigned,unsigned,unsigned>(255,0,0);break;
//    case 3: led_cmd.led["middle"].colors=std::make_tuple<unsigned,unsigned,unsigned>(255,0,0);break;
//    case 4: led_cmd.led["right"].colors=std::make_tuple<unsigned,unsigned,unsigned>(255,0,0);break;
//    case 5: led_cmd.led["far-right"].colors=std::make_tuple<unsigned,unsigned,unsigned>(255,0,0);break;
//    default:break;
//    }
//    this->led_selector++;
//    if(this->led_selector>5){
//        this->led_selector=1;
//    }

//    this->color++;
//    if(this->color==256){
//        this->color=0;
//    }
//    return led_cmd;
//}



}
