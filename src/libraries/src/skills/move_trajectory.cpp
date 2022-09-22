#include "mios/skills/move_trajectory.hpp"
#include <spdlog/spdlog.h>
#include "mios/strategies/read_from_file_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/strategies/ff_strategy.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mios/strategies/move_to_joint_pose.hpp"

namespace mios {

bool SkillParametersMoveTrajectory::from_json(const nlohmann::json &p){
    if(!mirmi_utils::read_json_param(p,"file",file)){
        spdlog::error("Parameter file could not be loaded but is mandatory.");
        return false;
    }
    if(!mirmi_utils::read_json_param(p,"plane",plane)){
        plane=false;
    }
    if(!mirmi_utils::read_json_param<double,6,1>(p,"F_ff",F_ff)){
        F_ff.setZero();
    }
    if(!mirmi_utils::read_json_param(p,"joint_mode",joint_mode)){
        joint_mode = false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersMoveTrajectory::get_parameter_list(){
    return {{"file",{}},{"plane",{}},{"F_ff",{}},{"joint_mode",{}}};
}

MoveTrajectory::MoveTrajectory(const std::string &id, Memory *memory, Portal* portal):Skill("MoveTrajectory",{},id,memory,portal,{ControlMode::mCartTorque, ControlMode::mJointTorque}),
m_finished(false){
    std::shared_ptr<SkillParametersMoveTrajectory> skill_params = get_parameters<SkillParametersMoveTrajectory>();
    m_file=skill_params->file;
    if(skill_params->joint_mode){
        read_trajectory_from_file(m_file, m_data_joint);
    }
    else{
        read_trajectory_from_file(m_file, m_data);
    }
    
}

std::shared_ptr<ManipulationPrimitive> MoveTrajectory::get_initial_mp(const Percept &p_0){
    std::shared_ptr<SkillParametersMoveTrajectory> skill_params = get_parameters<SkillParametersMoveTrajectory>();

    std::ifstream f(skill_params->file);
    std::string line;
    std::getline(f, line);
    std::istringstream ss(line);
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move_init",p_0);
    if(skill_params->joint_mode){
        std::array<double,7> T;
        ss >> T[0] >> T[1] >> T[2] >> T[3] >> T[4] >> T[5] >> T[6] ;
        Eigen::Matrix<double,7,1> T_g=Eigen::Matrix<double,7,1>(T.data());
        mp->create_strategy<MoveToJointPoseStrategy>("move",1);
        double speed;
        double acc;
        speed = m_memory->read_parameters()->user.dq_default;
        acc = m_memory->read_parameters()->user.ddq_default;
        mp->get_strategy<MoveToJointPoseStrategy>("move")->set_goal(T_g,speed,acc);
    }
    else{
        std::array<double,16> T;
        ss >> T[0] >> T[1] >> T[2] >> T[3] >> T[4] >> T[5] >> T[6] >> T[7] >> T[8] >> T[9] >> T[10] >> T[11] >> T[12] >> T[13] >> T[14] >> T[15];
        Eigen::Matrix<double,4,4> T_g=Eigen::Matrix<double,4,4>(T.data());
        mp->create_strategy<MoveToPoseStrategy>("move",1);
        Eigen::Matrix<double,2,1> speed;
        Eigen::Matrix<double,2,1> acc;
        speed<<m_memory->read_parameters()->user.dX_default;
        acc<<m_memory->read_parameters()->user.ddX_default;
        mp->get_strategy<MoveToPoseStrategy>("move")->set_goal(T_g,speed,acc);
        Eigen::Matrix<double,2,1> scale;
        scale<<1,1;
        mp->get_strategy<MoveToPoseStrategy>("move")->set_scale(scale);
    }
    return mp;
}

std::optional<std::shared_ptr<ManipulationPrimitive> > MoveTrajectory::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="move_init"){
        if(get_active_mp()->get_strategy_interface("move")->finished() && !m_finished){
            m_t_finished=std::chrono::high_resolution_clock::now();
            m_finished=true;
        }
        if(m_finished && std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_t_finished).count()>=1000){
            std::shared_ptr<SkillParametersMoveTrajectory> skill_params = get_parameters<SkillParametersMoveTrajectory>();
            std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p);
            mp->create_strategy<ReadFromFileStrategy>("move",1);
            if(skill_params->joint_mode){
                mp->get_strategy<ReadFromFileStrategy>("move")->set_data(m_data_joint);
                mp->get_strategy<ReadFromFileStrategy>("move")->set_joint_mode();
            }
            else{
                mp->get_strategy<ReadFromFileStrategy>("move")->set_data(m_data);
                            
                mp->create_strategy<FFStrategy>("feed_forward",1);
                mp->get_strategy<FFStrategy>("feed_forward")->set_TF_F_ff(skill_params->F_ff,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
                mp->get_strategy<FFStrategy>("feed_forward")->set_frame(true);
                if(skill_params->plane){
                    mp->create_strategy<CartComplianceStrategy>("compliance",1);
                    Eigen::Matrix<double,6,1> K_x_0;
                    Eigen::Matrix<double,6,1> xi_x_0;
                    K_x_0=m_memory->read_parameters()->control.cart_imp.K_x;
                    xi_x_0=m_memory->read_parameters()->control.cart_imp.xi_x;
                    K_x_0(2)=0;
                    xi_x_0(2)=0;
                    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x_0,xi_x_0);
                }
            }

            return mp;
        }
    }
    return {};
}

bool MoveTrajectory::check_local_suc_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="move"){
        return get_active_mp()->get_strategy<ReadFromFileStrategy>("move")->finished();
    }
    return false;
}

bool MoveTrajectory::read_trajectory_from_file(const std::string &file, std::vector<std::array<double, 16> > &data){
    std::ifstream ifile(file, std::ios::in);
    data.resize(0);

    //check to see that the file was opened correctly:
    if (!ifile.is_open()) {
        std::cerr << "There was a problem opening the input file!\n";
        return false;
    }

    std::string line;
    while (std::getline(ifile, line)) {
        std::istringstream ss(line);
        std::array<double,16> matrix;
        ss >> matrix[0] >> matrix[1] >> matrix[2] >> matrix[3] >> matrix[4] >> matrix[5] >> matrix[6] >> matrix[7] >> matrix[8] >> matrix[9] >> matrix[10] >> matrix[11] >> matrix[12] >> matrix[13] >> matrix[14] >> matrix[15];
        data.push_back(matrix);
    }

    return true;

}
bool MoveTrajectory::read_trajectory_from_file(const std::string &file, std::vector<std::array<double, 7> > &data){  // joint_mode
    std::ifstream ifile(file, std::ios::in);
    data.resize(0);

    //check to see that the file was opened correctly:
    if (!ifile.is_open()) {
        std::cerr << "There was a problem opening the input file!\n";
        return false;
    }

    std::string line;
    while (std::getline(ifile, line)) {
        std::istringstream ss(line);
        std::array<double,7> matrix;
        ss >> matrix[0] >> matrix[1] >> matrix[2] >> matrix[3] >> matrix[4] >> matrix[5] >> matrix[6] ;
        data.push_back(matrix);
    }

    return true;

}

}

