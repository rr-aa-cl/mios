#include "mios/skills/draw.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mios/strategies/twist_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/strategies/move_to_pose_chain_strategy.hpp"
#include "mios/strategies/ff_strategy.hpp"

namespace mios{


bool SkillParametersDraw::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param(parameters,"path_file",path_file)){
        spdlog::error("Parameter path_file could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"f_draw",f_draw)){
        spdlog::error("Parameter f_draw could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"file_mode",file_mode)){
        spdlog::error("Parameter file_mode could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"port_src",port_src)){
        spdlog::error("Parameter port_src could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"surface_distance",surface_distance)){
        spdlog::error("Parameter surface_distance could not be loaded but is mandatory.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"contact_speed",contact_speed)){
        spdlog::error("Parameter contact_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"contact_acc",contact_acc)){
        spdlog::error("Parameter contact_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"draw_speed",draw_speed)){
        spdlog::error("Parameter draw_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"draw_acc",draw_acc)){
        spdlog::error("Parameter draw_acc could not be loaded but is mandatory.");
        return false;
    }

    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersDraw::get_parameter_list(){
    return {{"path_file",{}},{"f_draw",{}},{"file_mode",{}},{"port_src",{}},{"surface_distance",{}},{"approach_speed",{}},{"approach_acc",{}},{"contact_speed",{}},{"contact_acc",{}},{"draw_speed",{}},{"draw_acc",{}}};
}

Draw::Draw(const std::string &name, Memory *memory,Portal* portal):Skill("Draw",{"Surface","Pen"},name,memory,portal,{ControlMode::mCartTorque}){
    m_position_cnt=0;
    std::shared_ptr<SkillParametersDraw> skill_params = get_parameters<SkillParametersDraw>();
    if(skill_params->file_mode){
        if(!load_data(skill_params->path_file)){
            spdlog::error("Draw skill: Could not load image data.");
            throw SkillException();
        }
        if(!check_data()){
            spdlog::error("Draw skill: Image check revealed errors.");
            throw SkillException();
        }
    }
}

Eigen::Matrix<double, 3, 3> Draw::get_O_R_T_0([[maybe_unused]] const Percept &p) const{
    return get_object("Surface")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> Draw::get_initial_mp(const Percept &p_0){
    return create_approach_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Draw::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_draw_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="draw"){
        if(get_active_mp()->get_strategy_interface("draw")->finished()){
            return create_retract_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="retract"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_approach_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> Draw::create_approach_mp(const Percept &p){
    spdlog::trace("Draw::create_approach_mp");
    std::shared_ptr<SkillParametersDraw> skill_params = get_parameters<SkillParametersDraw>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,3,1> approach_position = m_positions[m_position_cnt];
    Eigen::Matrix<double,4,4> T_a = from_image_to_world(approach_position);
    T_a(2,3)-=skill_params->surface_distance;
    move->set_goal(T_a,skill_params->approach_speed,skill_params->approach_acc);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(m_memory->read_parameters()->control.cart_imp.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> Draw::create_contact_mp(const Percept &p){
    spdlog::trace("Draw::create_contact_mp");
    std::shared_ptr<SkillParametersDraw> skill_params = get_parameters<SkillParametersDraw>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    dX_d<<0,0,skill_params->contact_speed(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->contact_acc);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(m_memory->read_parameters()->control.cart_imp.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> Draw::create_draw_mp(const Percept& p){
    spdlog::trace("Draw::create_draw_mp");
    std::vector<Eigen::Matrix<double,4,4> > draw_poses;
    draw_poses.push_back(from_image_to_world(m_positions[m_position_cnt]));
    for(unsigned i=m_position_cnt+1;i<m_positions.size();i++){
        if(m_start_positions[i]){
            break;
        }
        draw_poses.push_back(from_image_to_world(m_positions[i]));
        m_position_cnt=i;
    }
    m_position_cnt++;
    std::shared_ptr<SkillParametersDraw> skill_params = get_parameters<SkillParametersDraw>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("draw",p);
    mp->create_strategy<MoveToPoseChainStrategy>("draw",1);
    std::shared_ptr<MoveToPoseChainStrategy> draw = mp->get_strategy<MoveToPoseChainStrategy>("draw");
    draw->set_goal(draw_poses,skill_params->draw_speed,skill_params->draw_acc);
    mp->create_strategy<FFStrategy>("push",1);
    std::shared_ptr<FFStrategy> push = mp->get_strategy<FFStrategy>("push");
    Eigen::Matrix<double,6,1> T_F_ff;
    T_F_ff<<0,0,skill_params->f_draw,0,0,0;
    push->set_TF_F_ff(T_F_ff,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    Eigen::Matrix<double,6,1> K_x,xi_x;
    K_x=m_memory->read_parameters()->control.cart_imp.K_x;
    K_x(2)=0;
    xi_x=m_memory->read_parameters()->control.cart_imp.xi_x;
    xi_x(2)=0;
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x,xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> Draw::create_retract_mp(const Percept &p){
    spdlog::trace("Draw::create_retract_mp");
    std::shared_ptr<SkillParametersDraw> skill_params = get_parameters<SkillParametersDraw>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a = p.proprioception.T_T_EE;
    T_a(2,3)-=skill_params->surface_distance;
    move->set_goal(T_a,skill_params->approach_speed,skill_params->approach_acc);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(m_memory->read_parameters()->control.cart_imp.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

Eigen::Matrix<double,4,4> Draw::from_image_to_world(const Eigen::Matrix<double, 3, 1> &position){
    Eigen::Matrix<double,4,4> T_T_EE=get_object_pose_T("Surface");
    T_T_EE.block<3,1>(0,3)+=position;
    return T_T_EE;
}

bool Draw::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Pen")->name){
        spdlog::error("Draw skill: I have not grasped the pen.");
        return false;
    }
    return true;
}

bool Draw::check_local_suc_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="retract" && m_position_cnt >= m_positions.size()-1){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return true;
        }
    }
    return false;
}

bool Draw::check_local_err_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="draw"){
        //        if(p.proprioception.TF_F_ext_K(2)<m_memory->read_parameters()->user.F_ext_contact(0)){
        //            return true;
        //        }
    }
    return false;
}

bool Draw::load_data(const std::string &file_path){
    std::ifstream ifile(file_path, std::ios::in);
    m_positions.resize(0);
    m_start_positions.resize(0);

    //check to see that the file was opened correctly:
    if (!ifile.is_open()) {
        std::cerr << "There was a problem opening the input file!\n";
        return false;
    }

    std::string line;
    while (std::getline(ifile, line)) {
        std::istringstream ss(line);
        Eigen::Matrix<double,3,1> positions;
        double start;
        ss >> positions[0] >> positions[1] >> positions[2] >> start;
        m_positions.push_back(positions);
        m_start_positions.push_back(static_cast<bool>(start));
    }

    return true;
}

bool Draw::check_data(){
    for(unsigned i=1;i<m_start_positions.size();i++){
        if(m_start_positions[i-1] && m_start_positions[i]){
            spdlog::error("Draw skill: There cannot be two start positions in a row.");
            return false;
        }
    }
    return true;
}


}
