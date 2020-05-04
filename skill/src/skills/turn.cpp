#include "skills/turn.hpp"
namespace mios{
turn::turn():Skill("turn"){}
bool turn::read_skill_parameters(const nlohmann::json& p){
    std::shared_ptr<ConfigSkill_turn> c = std::static_pointer_cast<ConfigSkill_turn>(this->_config);

    if(!msrm_utils::read_json_param<double,1,1>(p,"F_d",c->F_z)){
        c->F_z.setZero();
    };
    if(!msrm_utils::read_json_param<double,1,1>(p,"speed",c->speed)){
        c->speed.setZero();
    };
    if(!msrm_utils::read_json_param<double,1,1>(p,"angle",c->angle)){
        c->angle.setZero();
    };
    if(!msrm_utils::read_json_param(p,"clockwise",c->clockwise)){
        msrm_utils::print_error("Missing parameter: clockwise");
        return false;
    }
    return true;

}
void turn::build_primitives(const Percept& p){
    this->insert_mp<mp_basic>("turn",p);
    this->set_init_mp("turn");

    std::shared_ptr<ConfigSkill_turn> c = std::static_pointer_cast<ConfigSkill_turn>(this->_config);
    std::shared_ptr<ConfigMP_mp_basic> c_turn = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("turn")->get_config());

    std::shared_ptr<AttractorBasic> attr_turn=std::static_pointer_cast<AttractorBasic>(this->get_mp("turn")->get_attractor());

    if(!c->clockwise){
        c->angle(0)*=-1;
    }

    Eigen::Matrix<double,3,3> R_lock = msrm_utils::eulerRPY_to_mat(0,0,c->angle(0))*p.TF_T_EE.block<3,3>(0,0);
    attr_turn->attr_pose=msrm_utils::concatenate_matrix(R_lock,p.TF_T_EE.block<3,1>(0,3));
    attr_turn->attr_ff<<0,0,c->F_z,0,0,0;

    c_turn->dX_d<<c->user.dX_max(0)*c->speed(0),c->user.dX_max(1)*c->speed(0);
    c_turn->ddX_d<<c->user.ddX_max(0),c->user.ddX_max(1);

}
std::tuple<bool,std::string> turn::check_edges(const Percept& p){return std::tuple<bool,std::string>(false,"");}
bool turn::check_local_suc_conditions(const Percept& p){
    return this->get_mp("turn")->in_attractor(p);
}
void turn::evaluate(){
    this->_eval.cost_err=this->_eval.p_1.time-this->_eval.p_0.time;
    this->_eval.cost_suc=0;
}
void turn::create_config(){
this->_config=std::make_shared<ConfigSkill_turn>();
}
Eigen::Matrix<double,3,3> turn::get_O_R_TF(const Percept &p){
    return p.O_T_EE.block<3,3>(0,0);
}
}
