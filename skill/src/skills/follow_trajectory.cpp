#include "skills/follow_trajectory.hpp"
namespace mios{
follow_trajectory::follow_trajectory():Skill("follow_trajectory"){}

bool follow_trajectory::read_skill_parameters(const nlohmann::json& p){
    std::shared_ptr<ConfigSkill_follow_trajectory> c_skill = std::static_pointer_cast<ConfigSkill_follow_trajectory>(this->_config);
    msrm_utils::read_json_param<double,2,1>(p,"speed",c_skill->speed);
    msrm_utils::read_json_param<double,2,1>(p,"acc",c_skill->acc);
    if(!msrm_utils::read_json_param<std::string>(p,"locations",c_skill->locations)){
        c_skill->locations.resize(0);
    }
    msrm_utils::read_json_param(p,"flag_cart",c_skill->flag_cart);
    msrm_utils::read_json_param(p,"t_settle",c_skill->t_settle);
    return true;
}

void follow_trajectory::build_primitives(const Percept& p){
    this->_cnt_mp=0;
    this->_t_settle=0;
    std::shared_ptr<ConfigSkill_follow_trajectory> c_skill = std::static_pointer_cast<ConfigSkill_follow_trajectory>(this->_config);
    std::cout<<"flag: "<<c_skill->flag_cart<<std::endl;
    std::cout<<"loc: "<<c_skill->locations[0]<<std::endl;
    std::cout<<"loc2: "<<c_skill->locations[1]<<std::endl;
    if(c_skill->flag_cart){
        for(unsigned i=0;i<c_skill->locations.size();i++){
            std::string mp_name="move_to_pose_"+std::to_string(i);
            this->insert_mp<mp_basic>(mp_name,p);
            std::shared_ptr<ConfigMP_mp_basic> c_mp = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp(mp_name)->get_config());

            c_mp->dX_d<<c_skill->speed(0)*c_skill->user.dX_max(0),c_skill->speed(0)*c_skill->user.dX_max(1);
            c_mp->ddX_d<<c_skill->acc(0)*c_skill->user.ddX_max(0),c_skill->acc(0)*c_skill->user.ddX_max(1);

            std::shared_ptr<AttractorBasic> attr_move_to_pose=std::static_pointer_cast<AttractorBasic>(this->get_mp(mp_name)->get_attractor());
            attr_move_to_pose->attr_vel<<0,0,0,0,0,0;
            Object o;
            if(!this->_kb->load_object(c_skill->locations[i],o)){
                msrm_utils::print_warning("Could not load object" + o.name);
            }
            attr_move_to_pose->attr_pose=this->_kb->transform_to_EE(o.TF_T_o(this->_config->frames.O_R_TF));
        }
    }else{
        for(unsigned i=0;i<c_skill->locations.size();i++){
            std::string mp_name="move_to_pose_"+std::to_string(i);
            this->insert_mp<mp_basic_joint>(mp_name,p);
            std::shared_ptr<ConfigMP_mp_basic_joint> c_mp = std::static_pointer_cast<ConfigMP_mp_basic_joint>(this->get_mp(mp_name)->get_config());

            c_mp->dq_d<<c_skill->speed(0)*c_skill->user.dq_max(0);
            c_mp->ddq_d<<c_skill->acc(0)*c_skill->user.ddq_max(0);

            std::shared_ptr<AttractorBasicJoint> attr_move_to_pose=std::static_pointer_cast<AttractorBasicJoint>(this->get_mp(mp_name)->get_attractor());
            attr_move_to_pose->attr_vel<<0,0,0,0,0,0,0;
            Object o;
            if(!this->_kb->load_object(c_skill->locations[i],o)){
                msrm_utils::print_warning("Could not load object" + o.name);
            }
            attr_move_to_pose->attr_pose=o.q_o;
            std::cout<<"QG: "<<attr_move_to_pose->attr_pose<<std::endl;
        }
    }
    if(c_skill->locations.size()>0){
        this->set_init_mp("move_to_pose_0");
    }else{
        msrm_utils::print_error("No location provided.");
    }
}
std::tuple<bool,std::string> follow_trajectory::check_edges(const Percept& p){
    std::shared_ptr<ConfigSkill_follow_trajectory> c_skill = std::static_pointer_cast<ConfigSkill_follow_trajectory>(this->_config);
    if(this->_cnt_mp<c_skill->locations.size()-1){
        if(this->get_mp("move_to_pose_"+std::to_string(this->_cnt_mp))->in_attractor(p)){
            this->_cnt_mp++;
            return std::tuple<bool,std::string>(true,"move_to_pose_"+std::to_string(this->_cnt_mp));
        }
    }else{
        return std::tuple<bool,std::string>(false,"move_to_pose_"+std::to_string(this->_cnt_mp+1));
    }
    return std::tuple<bool,std::string>(false,"move_to_pose_"+std::to_string(this->_cnt_mp+1));
}

bool follow_trajectory::check_local_suc_conditions(const Percept& p){
    std::shared_ptr<ConfigSkill_follow_trajectory> c_skill = std::static_pointer_cast<ConfigSkill_follow_trajectory>(this->_config);
    if(this->get_mp("move_to_pose_"+std::to_string(c_skill->locations.size()-1))->in_attractor(p) && !this->_flag_settle){
        this->_flag_settle=true;
    }
    if(this->_flag_settle){
        this->_t_settle+=0.001;
    }
    return this->get_mp("move_to_pose_"+std::to_string(c_skill->locations.size()-1))->in_attractor(p);
}

bool follow_trajectory::check_local_ex_conditions(const Percept &p){
    std::shared_ptr<ConfigSkill_follow_trajectory> c_skill=std::static_pointer_cast<ConfigSkill_follow_trajectory>(this->_config);
    return this->_t_settle>c_skill->t_settle;
}

void follow_trajectory::evaluate(){}
void follow_trajectory::create_config(){
    this->_config=std::make_shared<ConfigSkill_follow_trajectory>();
}
}
