#include "skills/button_pushing.hpp"
namespace mios{
button_pushing::button_pushing():Skill("button_pushing"){}
button_pushing::~button_pushing(){}
bool button_pushing::read_skill_parameters(const nlohmann::json& p){
    std::shared_ptr<ConfigSkill_button_pushing> c = std::static_pointer_cast<ConfigSkill_button_pushing>(this->_config);
    msrm_utils::read_json_param<double,1,1>(p,"acc",c->acc);
    msrm_utils::read_json_param<double,1,1>(p,"speed",c->speed);
    msrm_utils::read_json_param(p,"t_hold",c->t_hold);
    return true;
}

Eigen::Matrix<double, 3, 3> button_pushing::get_O_R_TF(const Percept &p){
    return this->get_object_pose("button",false).block<3,3>(0,0);
}

void button_pushing::build_primitives(const Percept& p){

    this->insert_mp<mp_basic>("push",p);
    this->insert_mp<mp_basic>("hold",p);
    this->insert_mp<mp_basic>("retreat",p);
    this->set_init_mp("push");

    std::shared_ptr<ConfigSkill_button_pushing> c = std::static_pointer_cast<ConfigSkill_button_pushing>(this->_config);

    std::shared_ptr<ConfigMP_mp_basic> c_push = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("push")->get_config());
    std::shared_ptr<ConfigMP_mp_basic> c_hold = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("hold")->get_config());
    std::shared_ptr<ConfigMP_mp_basic> c_retreat = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("retreat")->get_config());

    this->_push_blind=false;

    this->_button_height=0;
    Object button = this->get_object("button");
    if(button.geometry.find("radius")==button.geometry.end()){
        msrm_utils::print_warning("I do not know the radius of the button. I will assume 0.005 m.");
        this->_button_radius=0.005;
    }else{
        if(!msrm_utils::read_json_param(button.geometry,"radius",this->_button_radius)){
            throw SkillException("Cannot read radius from object "+button.name+".");
        }
    }
    if(button.geometry.find("height")==button.geometry.end()){
        msrm_utils::print_warning("I do not know the height of the button. I will push until sufficient resistance occurs.");
        this->_push_blind=true;
    }else{
        if(!msrm_utils::read_json_param(button.geometry,"height",this->_button_height)){
            throw SkillException("Cannot read height from object "+button.name+".");
        }
    }
    Eigen::Matrix<double,4,4> button_pose = this->get_object_pose("button");
    Eigen::Matrix<double,4,4> button_pose_pressed =  button_pose;
    button_pose_pressed(2,3)+=this->_button_height;

    std::shared_ptr<AttractorBasic> attr_push=std::static_pointer_cast<AttractorBasic>(this->get_mp("push")->get_attractor());
    std::shared_ptr<AttractorBasic> attr_hold=std::static_pointer_cast<AttractorBasic>(this->get_mp("hold")->get_attractor());
    std::shared_ptr<AttractorBasic> attr_retreat=std::static_pointer_cast<AttractorBasic>(this->get_mp("retreat")->get_attractor());
    if(!this->_push_blind){
        attr_push->attr_pose=button_pose_pressed;
        c_push->dX_d<<this->_config->user.dX_max(0)*c->speed(0),this->_config->user.dX_max(1);
        c_push->ddX_d<<this->_config->user.ddX_max(0)*c->acc(0),this->_config->user.ddX_max(1);
    }else{
        attr_push->attr_vel<<0,0,this->_config->user.dX_max(0)*c->speed(0),0,0,0;
    }
    attr_retreat->attr_pose=button_pose;
    c_retreat->dX_d<<this->_config->user.dX_max(0)*c->speed(0),this->_config->user.dX_max(1);
    c_retreat->ddX_d<<this->_config->user.ddX_max(0)*c->acc(0),this->_config->user.ddX_max(1);

}
std::tuple<bool,std::string> button_pushing::check_edges(const Percept& p){
    std::shared_ptr<ConfigSkill_button_pushing> c = std::static_pointer_cast<ConfigSkill_button_pushing>(this->_config);
    if(this->_active_mp->get_id()=="push"){
        if(!this->_push_blind){
            if(this->_active_mp->in_attractor(p)){
                this->_t_start_hold=p.time;
                return std::tuple<bool,std::string>(true,"hold");
            }
        }else{
            if(p.TF_F_ext(2)>this->_config->user.F_contact(2)*3){
                this->_t_start_hold=p.time;
                return std::tuple<bool,std::string>(true,"hold");
            }
        }
    }
    if(this->_active_mp->get_id()=="hold"){
        if(p.time>this->_t_start_hold+c->t_hold){
            return std::tuple<bool,std::string>(true,"retreat");
        }
    }
    return std::tuple<bool,std::string>(false,"");
}
bool button_pushing::check_local_suc_conditions(const Percept& p){
    if(this->_active_mp->get_id()=="retreat"){
        return true;
    }
    return false;
}

bool button_pushing::check_local_ex_conditions(const Percept &p){
    if(this->_active_mp->get_id()=="retreat"){
        if(this->_active_mp->in_attractor(p)){
            return true;
        }
    }
    return false;
}

bool button_pushing::check_local_err_conditions(const Percept &p){
    Eigen::Matrix<double,2,1> e;
    e<<p.TF_T_EE_d(0,3)-p.TF_T_EE(0,3),p.TF_T_EE_d(1,3)-p.TF_T_EE(1,3);
    double e_abs=msrm_utils::norm_2<2>(e);
    if(e_abs>this->_button_radius){
        return true;
    }
    return false;
}

void button_pushing::evaluate(){}
void button_pushing::create_config(){
    this->_config=std::make_shared<ConfigSkill_button_pushing>(ConfigSkill_button_pushing());
}
}
