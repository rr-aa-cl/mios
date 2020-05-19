#include "core/core.hpp"

#include <msrm_utils/math.hpp>
#include <msrm_utils/files.hpp>
#include <msrm_utils/network.hpp>
#include <msrm_utils/conversion.hpp>
#include <msrm_utils/json.hpp>
#include <msrm_utils/system.hpp>
#include "utils/exceptions.hpp"
#include "skill/skill.hpp"
#include "skills/nullskill.hpp"
#include "event_publisher/event_publisher.hpp"

#include <iostream>
#include <chrono>
#include <fstream>
#include <thread>

#include <pwd.h>
#include <signal.h>
#include <stdio.h>
#include <limits.h>
#include <unistd.h>
#include <functional>

#include <SDL2/SDL.h>
#include <SDL2/SDL_mixer.h>

#include <spdlog/spdlog.h>

namespace mios {

Core::Core(int argc, char **argv):m_active_skill(std::make_shared<NullSkill>(&m_memory,std::make_shared<SkillParametersNullSkill>())){

    this->_config_internal.path_executable=msrm_utils::get_path_executable(argv);
    this->_config_internal.grasped_object="none";

    spdlog::info("Initializing knowledgebase...");
    if(!m_memory.initialize(this->_config_internal)){
        spdlog::error("Could not initialize knowledge base, shutting down. Mongodb service must run on port 27017. Check status with <systemctl status mongodb.service>.");
        exit(-1);
    }

    spdlog::info("Initializing MIOS core...");
    if(!this->initialize()){
        spdlog::warn("Could not initialize MIOS core. I may be able to recover...");
    }
}

Core::~Core(){
    terminate();
}

bool Core::initialize(){
    if(!m_memory.load_parameters()){
        spdlog::error("Could not load all parameters. Robot is not operational.");
        return false;
    }

    std::optional<std::string> panda_ip = m_panda_body.get_robot_ip(m_memory.read_parameters()->system.robot_ip);

    if(m_memory.read_parameters()->system.has_robot){
        if(!m_panda_body.connect_to_robot(panda_ip.value())){
            return false;
        }
    }
    if(m_memory.read_parameters()->system.has_gripper){
        if(!m_panda_body.connect_to_gripper(panda_ip.value())){
            return false;
        }
    }
    return true;
}

void Core::terminate(){
    m_panda_body.disconnect_from_robot();
    m_panda_body.disconnect_from_gripper();
}

bool Core::has_terminated() const{
    return this->_flag_stop_control;
}

bool Core::reset(){
    if(!m_memory.load_parameters()){
        return false;
    }
    spdlog::info("Core reset finished.");
    return true;
}

Memory* Core::get_memory(){
    return &m_memory;
}

bool Core::load_skill(std::shared_ptr<Skill> skill){
    spdlog::info("Loading skill "+skill->get_id()+".");
    // set active skill and setup
    m_active_skill=skill;
    refresh_percept({});
    m_active_skill->write_O_R_TF_to_config(m_percept);
    refresh_percept(m_active_skill->get_config<>()->frames.O_R_TF);
    m_percept.controller.K_x=m_active_skill->get_config<>()->controller.K_0;
    m_percept.controller.xi_x=m_active_skill->get_config<>()->controller.xi;
    m_percept.controller.K_theta=m_active_skill->get_config<>()->controller.K_theta;
    m_percept.controller.xi_theta=m_active_skill->get_config<>()->controller.xi_theta;
    spdlog::info("Applying skill context...");
    m_memory.apply_skill_context(m_active_skill->get_id());
    spdlog::info("Initializing skill...");
    if(!m_active_skill->initialize(m_percept)){
        return false;
    }
    return true;
}

void Core::unload_skill(){
    m_active_skill=std::make_shared<NullSkill>(&m_memory,std::make_shared<SkillParametersNullSkill>());
    _flag_stop_control=false;
}

bool Core::execute_skill(){
    spdlog::debug("CORE: execute_skill");

    if(!m_panda_body.pre_run_checks()){
        if(!m_panda_body.recover()){
            return false;
        }
    }

    spdlog::debug("CORE: start_control_cycle: while-loop");
    this->_tau_J_old={0,0,0,0,0,0,0};
    refresh_percept(m_active_skill->get_config<>()->frames.O_R_TF);
    ConfigController config_controller = m_active_skill->get_config<>()->controller;
    ConfigUser config_user = m_active_skill->get_config<>()->user;
    ConfigFrames config_frames = m_active_skill->get_config<>()->frames;

    std::array<double,3> load_com = msrm_utils::convert_to_array<double,3,1>(config_user.load_com);
    std::array<double,9> load_I = msrm_utils::convert_to_array<double,3,3>(config_user.load_I);
    std::array<double,7> tau_contact = msrm_utils::convert_to_array<double,7,1>(config_user.tau_contact);
    std::array<double,7> tau_max = msrm_utils::convert_to_array<double,7,1>(config_user.tau_max);
    std::array<double,6> F_contact = msrm_utils::convert_to_array<double,6,1>(config_user.F_contact);
    std::array<double,6> F_max = msrm_utils::convert_to_array<double,6,1>(config_user.F_max);
    std::array<double,16> EE_T_K = msrm_utils::convert_to_array<double,4,4>(config_frames.EE_T_K);
    std::array<double,7> K_theta = msrm_utils::convert_to_array<double,7,1>(config_controller.K_theta);
    std::array<double,6> K_x = msrm_utils::convert_to_array<double,6,1>(config_controller.K_0);
    std::array<double,16> F_T_EE = msrm_utils::convert_to_array<double,4,4>(config_frames.F_T_EE);

    if(!m_panda_body.set_robot_parameters(config_user.load_m,load_com,load_I,tau_contact,tau_max,F_contact,F_max,EE_T_K,K_x,K_theta,F_T_EE)){
        return false;
    }

    bool result;
    if(this->_kb.get_local_memory()->access_config_general().control_mode==ControlMode::mCartTorque){

        m_controller_pipeline=std::make_unique<CartTorqueControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,&_kb);
        result=m_panda_body.torque_control(std::bind(&Core::cart_torque_controller_pipeline,this,std::placeholders::_1));
    }

    m_controller_pipeline->terminate();
    return result;
}

void Core::terminate_control_cycle(){
    this->_flag_stop_control=true;
}

franka::Finishable* Core::control_base_cycle(const franka::RobotState& state){

    franka::GripperState gripper_state;
    m_percept.update(m_panda_body.get_panda_model(),state,gripper_state,m_active_skill->get_config<>()->frames.O_R_TF);
    Actuator* cmd=m_active_skill->cycle(m_percept);
    franka::Finishable* panda_cmd=m_controller_pipeline->step(m_percept,*cmd);
    m_controller_pipeline->update_percept(m_percept.controller);
    if(cmd->is_stopped()){
        panda_cmd->motion_finished=true;
    }
    return panda_cmd;
}

franka::Torques Core::cart_torque_controller_pipeline(const franka::RobotState& state){
    return *static_cast<franka::Torques*>(control_base_cycle(state));
}

//franka::Torques Core::control_cycle_torque_joint(const franka::RobotState state){
//    auto t_s_start = std::chrono::system_clock::now();
//    CmdSkill cmd_skill;
//    if(!this->control_base_cycle(state,cmd_skill)){
//        franka::Torques tau={0,0,0,0,0,0,0};
//        return franka::MotionFinished(tau);
//    }

//    this->input_control_joint_imp(this->_percept);
//    this->input_virtual_walls_joint(this->_percept);
//    this->input_control_nullspace(this->_percept);

//    this->_in_u_joint_imp.theta_d=cmd_skill.q_d;
//    this->_in_u_joint_imp.tau_ff=cmd_skill.tau_ff;
//    this->_in_u_joint_imp.K_theta=cmd_skill.K_theta;
//    this->_in_u_joint_imp.D_theta=cmd_skill.xi_theta;

//    this->_cntr_joint_imp.step(this->_in_u_joint_imp,this->_out_y_joint_imp);

//    this->_percept.K_theta=this->_cntr_joint_imp.get_out_l().K_theta;
//    this->_percept.xi_theta=this->_cntr_joint_imp.get_out_l().D_theta;

//    if(this->_kb.get_local_memory()->access_config_cntr().virt_walls_joint_on){
//        this->_virt_walls_joint.step(this->_in_u_virt_walls_joint,this->_out_y_virt_walls_joint);
//    }

//    bool walls_joint_valid = this->validity_check_virtual_walls_joint();

//    if(this->_kb.get_local_memory()->access_config_cntr().nullspace_cntr_on){
//        this->_cntr_nullsp_q.step(this->_in_u_cntr_nullsp_q,this->_out_y_cntr_nullsp_q);
//        this->_in_u_cntr_nullsp_proj.tau_c=this->_out_y_cntr_nullsp_q.tau_J_d;
//        this->_cntr_nullsp_proj.step(this->_in_u_cntr_nullsp_proj,this->_out_y_cntr_nullsp_proj);
//    }

//    for(unsigned i=0;i<7;i++){
//        this->_in_u_mux.tau_J_d(i)=this->_out_y_joint_imp.tau_J_d(i);
//        if(this->get_kb()->get_local_memory()->access_config_cntr().virt_walls_joint_on && walls_joint_valid){
//            this->_in_u_mux.tau_J_d(i)+=this->_out_y_virt_walls_joint.tau_vwalls(i);
//        }
//        if(this->get_kb()->get_local_memory()->access_config_cntr().nullspace_cntr_on){
//            this->_in_u_mux.tau_J_d(i)+=this->_out_y_cntr_nullsp_proj.tau_n(i);
//        }
//    }

//    this->_cntr_mux.step(this->_in_u_mux,this->_out_y_mux);

//    franka::Torques tau_J_checked={this->_out_y_mux.tau_J_d_checked[0],this->_out_y_mux.tau_J_d_checked[1],this->_out_y_mux.tau_J_d_checked[2],
//                                   this->_out_y_mux.tau_J_d_checked[3],this->_out_y_mux.tau_J_d_checked[4],this->_out_y_mux.tau_J_d_checked[5],
//                                   this->_out_y_mux.tau_J_d_checked[6]};

//    if(!this->validity_check_torque(tau_J_checked.tau_J)){
//        this->terminate_control_cycle();
//    }

//    auto t_s_end = std::chrono::system_clock::now();

//    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

//    if(this->_flag_stop_control){
//        spdlog::info("Controller cycle has been terminated.");
//        return franka::MotionFinished(tau_J_checked);
//    }
//    if(this->_kb.get_local_memory()->access_config_general().safe_mode){
//        std::cout<<"tau_J=["<<tau_J_checked.tau_J[0]<<","<<tau_J_checked.tau_J[1]<<","<<tau_J_checked.tau_J[2]<<","<<tau_J_checked.tau_J[3]
//                <<","<<tau_J_checked.tau_J[4]<<","<<tau_J_checked.tau_J[5]<<","<<tau_J_checked.tau_J[6]<<"]"<<std::endl;
//        spdlog::info("Cycle time: "+std::to_string(t));
//        tau_J_checked.tau_J={0,0,0,0,0,0,0};
//    }
//    this->_tau_J_last=tau_J_checked.tau_J;

//    return tau_J_checked;
//}

//franka::CartesianVelocities Core::control_cycle_velocity_cart(const franka::RobotState state){

//    auto t_s_start = std::chrono::system_clock::now();
//    CmdSkill cmd_skill;
//    if(!this->control_base_cycle(state,cmd_skill)){
//        franka::CartesianVelocities O_dP_EE_d={0,0,0,0,0,0};
//        return franka::MotionFinished(O_dP_EE_d);
//    }
//    this->check_cartesian_velocity_workspace(cmd_skill.TF_dX_d,this->_percept);
//    this->base_avoidance(cmd_skill.TF_dX_d,this->_percept);

//    franka::CartesianVelocities O_dP_EE_d = msrm_utils::convert_to_array<double,6,1>(msrm_utils::rotate_vector(cmd_skill.TF_dX_d,this->_active_skill->get_config<>()->frames.O_R_TF));
//    if(!this->validity_check_velocity_cart(O_dP_EE_d.O_dP_EE)){
//        this->terminate_control_cycle();
//    }

//    auto t_s_end = std::chrono::system_clock::now();

//    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

//    if(this->_flag_stop_control){
//        spdlog::info("Controller cycle has been terminated.");
//        return franka::MotionFinished(O_dP_EE_d);
//    }
//    if(this->_kb.get_local_memory()->access_config_general().safe_mode){
//        std::cout<<"O_dP_EE_d=["<<O_dP_EE_d.O_dP_EE[0]<<","<<O_dP_EE_d.O_dP_EE[1]<<","<<O_dP_EE_d.O_dP_EE[2]<<","<<O_dP_EE_d.O_dP_EE[3]<<","<<O_dP_EE_d.O_dP_EE[4]<<","<<O_dP_EE_d.O_dP_EE[5]<<std::endl;
//        spdlog::info("Cycle time: "+std::to_string(t));
//        O_dP_EE_d={0,0,0,0,0,0};
//    }

//    return O_dP_EE_d;
//}

//franka::JointVelocities Core::control_cycle_velocity_joint(const franka::RobotState state){
//    auto t_s_start = std::chrono::system_clock::now();
//    CmdSkill cmd_skill;
//    if(!this->control_base_cycle(state,cmd_skill)){
//        franka::JointVelocities dq_d={0,0,0,0,0,0,0};
//        return franka::MotionFinished(dq_d);
//    }
//    franka::JointVelocities dq_d = msrm_utils::convert_to_array<double,7,1>(cmd_skill.dq_d);

//    if(!this->validity_check_velocity_joint(dq_d.dq)){
//        this->terminate_control_cycle();
//    }

//    auto t_s_end = std::chrono::system_clock::now();

//    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

//    if(this->_flag_stop_control){
//        return franka::MotionFinished(dq_d);
//    }
//    if(this->_kb.get_local_memory()->access_config_general().safe_mode){
//        std::cout<<"dq_d=["<<dq_d.dq[0]<<","<<dq_d.dq[1]<<","<<dq_d.dq[2]<<","<<dq_d.dq[3]<<","<<dq_d.dq[4]<<","<<dq_d.dq[5]<<","<<dq_d.dq[6]<<std::endl;
//        spdlog::info("Cycle time: "+std::to_string(t));
//        dq_d={0,0,0,0,0,0,0};
//    }

//    return dq_d;
//}

//void Core::cycle_led(std::function<LEDCmd(const Percept& p)> callback_led){
//    unsigned T;

//    while(true){
//        LEDCmd led_output = callback_led(this->_percept);
//        if(led_output.finished){
//            spdlog::info("Unloading LED pattern");
//            return;
//        }

//        if(led_output.f>0){
//            T=1/led_output.f*1000;
//        }
//        if(led_output.f<=0){
//            T=std::numeric_limits<unsigned>::max();
//        }
//        nlohmann::json request;
//        for(const auto& led : led_output.led){
//            nlohmann::json l;
//            l["colors"].emplace_back(std::get<0>(led.second.colors));
//            l["colors"].emplace_back(std::get<1>(led.second.colors));
//            l["colors"].emplace_back(std::get<2>(led.second.colors));
//            l["tt"]=led.second.tt;
//            l["id"]=this->_led_panel_id[led.first];
//            request.push_back(l);
//        }
//        nlohmann::json response;
//        msrm_utils::JsonRPCClient::call_method("localhost",9000,"set_led",request,response);

//        std::this_thread::sleep_for(std::chrono::milliseconds(T));
//        if(!this->_flag_run_led){
//            spdlog::info("LED thread has been stopped.");
//            return;
//        }
//    }
//}

//void Core::cycle_led_wrapper(std::shared_ptr<LEDPattern> p){
//    this->cycle_led(std::bind(&LEDPattern::cycle_led,p.get(),&this->_percept));
//}

//void Core::cycle_sound(std::function<SoundCmd(const Percept& p)> callback_sound){

//    while(true){
//        SoundCmd sound_output = callback_sound(this->_percept);
//        if(sound_output.f>10){
//            spdlog::warn("Setting the sound cycle frequency to more than 10 Hz may lead to undefined behavior.");
//        }
//        unsigned T;
//        if(sound_output.f>0){
//            T=1/sound_output.f*1000;
//        }
//        if(sound_output.f<=0){
//            T=std::numeric_limits<unsigned>::max();
//        }
//        if(!sound_output.update || sound_output.file==""){
//            continue;
//        }
//        std::string path=this->_config_internal.path_executable+"/../resources/audio/"+sound_output.file;
//        Mix_Music* music = Mix_LoadMUS(path.c_str());

//        if (music){
//            if (Mix_PlayMusic(music, 1) == 0){
//                while (Mix_PlayingMusic()){
//                    SDL_Delay(10);
//                    //                    boost::this_thread::interruption_point();
//                }
//            }
//            else{
//                std::cerr << "Mix_PlayMusic ERROR: " << Mix_GetError() << std::endl;
//            }

//            Mix_FreeMusic(music);
//            music = 0;
//        }
//        else{
//            std::cerr << "Mix_LoadMuS ERROR: " << Mix_GetError() << std::endl;
//        }
//        std::this_thread::sleep_for(std::chrono::milliseconds(T));
//        if(!this->_flag_run_sound){
//            Mix_HaltMusic();
//            spdlog::info("Sound thread has been stopped.");
//            return;
//        }
//    }
//}

//bool Core::set_grasped_object(const std::string &o){
//    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
//        return true;
//    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
//        spdlog::warn("Gripper not connected.");
//        return false;
//    }

//    Object obj;
//    if(!this->_kb.load_object(o,obj)){
//        spdlog::error("Cannot find object "+o+" in knowledge base.");
//        return false;
//    }
//    if(!this->lock_robot_connection(false)){
//        spdlog::error("Cannot access gripper, another process is blocking the FCI.");
//        return false;
//    }
//    bool result=false;
//    try{
//        nlohmann::json p;
//        p["grasped_object"]=o;
//        this->_kb.get_local_memory()->modify_hidden_config_user(p);
//        this->_percept.mios_state.grasped_object=o;
//        this->m_panda_body->setLoad(obj.mass,msrm_utils::convert_to_array<double,3,1>(obj.EE_ob_com),msrm_utils::convert_to_array<double,3,3>(obj.ob_I));
//        nlohmann::json p_frame;
//        msrm_utils::write_json_array<double,4,4>(p_frame["EE_T_TCP"],obj.EE_T_O);
//        result=true;
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }
//    if(!this->set_ee()){
//        spdlog::error("Could not set end effector configuration.");
//        result=false;
//    }
//    this->unlock_robot_connection();
//    return result;
//}


//bool Core::grasp_object(const std::string &o, double width, double speed, double force, bool check_width){
//    //    if(this->check_lockdown()){
//    //        spdlog::error("Core is under lockdown.");
//    //        return false;
//    //    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
//        return true;
//    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
//        spdlog::warn("Gripper not connected.");
//        return false;
//    }
//    if(!this->has_gripper_connection()){
//        spdlog::error("Cannot grasp object. I am currently not connection to the gripper.");
//        return false;
//    }
//    Object obj;
//    if(!this->_kb.load_object(o,obj)){
//        spdlog::error("Cannot find object "+o+" in knowledge base.");
//        return false;
//    }
//    if(!this->lock_robot_connection(false)){
//        spdlog::error("Cannot access gripper, another process is blocking the FCI.");
//        return false;
//    }
//    bool result=false;
//    try{
//        double max_width=this->m_panda_hand->readOnce().max_width;
//        double current_width=this->m_panda_hand->readOnce().width;
//        if(width==-1){
//            width=0;
//        }else{
//            if(width<0 || width>max_width){
//                spdlog::error("Gripper cannot reach width of "+std::to_string(width)+". Must be between 0 and "+std::to_string(max_width)+".");
//                this->unlock_robot_connection();
//                return false;
//            }
//            if(width>current_width){
//                spdlog::error("Grasping to a width larger than the current width is invalid.");
//                this->unlock_robot_connection();
//                return false;
//            }
//        }
//        if(!this->m_panda_hand->readOnce().is_grasped){
//            result=this->m_panda_hand->grasp(width,speed,force,1,1);
//        }else{
//            result=true;
//        }
//        franka::GripperState gripper_state=this->m_panda_hand->readOnce();
//        if(check_width && (gripper_state.width<obj.grasp_width-0.005 || gripper_state.width>obj.grasp_width+0.005)){
//            spdlog::error("Dimensions of object "+o+" not within expected limits. Expected: " + std::to_string(obj.grasp_width) + ", but measured: " + std::to_string(gripper_state.width));
//            this->m_panda_hand->move(current_width,1);
//            this->unlock_robot_connection();
//            return false;
//        }
//        nlohmann::json p;
//        p["grasped_object"]=o;
//        this->_kb.get_local_memory()->modify_hidden_config_user(p);
//        this->_percept.mios_state.grasped_object=o;
//        this->m_panda_body->setLoad(obj.mass,msrm_utils::convert_to_array<double,3,1>(obj.EE_ob_com),msrm_utils::convert_to_array<double,3,3>(obj.ob_I));
//        nlohmann::json p_frame;
//        msrm_utils::write_json_array<double,4,4>(p_frame["EE_T_TCP"],obj.EE_T_O);
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }catch(franka::InvalidOperationException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }
//    if(!this->set_ee()){
//        spdlog::error("Could not grasp. Error while setting end effector configuration.");
//        result=false;
//    }
//    this->unlock_robot_connection();
//    return result;
//}

//bool Core::home_gripper(){
//    //    if(this->check_lockdown()){
//    //        spdlog::error("Core is under lockdown.");
//    //        return false;
//    //    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
//        return true;
//    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
//        spdlog::warn("Gripper not connected.");
//        return false;
//    }
//    if(!this->has_gripper_connection()){
//        spdlog::error("Cannot home gripper. I am currently not connected to the gripper.");
//        return false;
//    }
//    if(!this->lock_robot_connection(false)) return false;
//    bool result=false;
//    try{
//        if(this->m_panda_hand->readOnce().is_grasped){
//            spdlog::error("Cannot home the gripper while grasping.");
//            result=false;
//        }else{
//            result=this->m_panda_hand->homing();
//        }
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }catch(franka::InvalidOperationException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }
//    this->unlock_robot_connection();
//    return result;
//}

//bool Core::grasp(double width, double speed, double force){
//    //    if(this->check_lockdown()){
//    //        spdlog::error("Core is under lockdown.");
//    //        return false;
//    //    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
//        spdlog::warn("Gripper not connected.");
//        return false;
//    }
//    if(!this->has_gripper_connection()){
//        spdlog::error("Cannot move gripper. I am currently not connected to the gripper.");
//        return false;
//    }
//    bool result=false;
//    try{
//        result=this->m_panda_hand->grasp(width,speed,force,1,1);
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//        return false;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//        return false;
//    }
//    return result;
//}

//bool Core::move_gripper(double width, double speed){
//    //    if(this->check_lockdown()){
//    //        spdlog::error("Core is under lockdown.");
//    //        return false;
//    //    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
//        spdlog::warn("Gripper not connected.");
//        return false;
//    }
//    if(!this->has_gripper_connection()){
//        spdlog::error("Cannot move gripper. I am currently not connected to the gripper.");
//        return false;
//    }
//    bool result=false;
//    try{
//        result=this->m_panda_hand->move(width,speed);
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//        return false;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//        return false;
//    }
//    return result;
//}

//bool Core::release_object(double width, double speed){
//    //    if(this->check_lockdown()){
//    //        spdlog::error("Core is under lockdown.");
//    //        return false;
//    //    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
//        return true;
//    }
//    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
//        spdlog::warn("Gripper not connected.");
//        return false;
//    }
//    if(!this->has_gripper_connection()){
//        spdlog::error("Cannot release object. I am currently not connected to the gripper.");
//        return false;
//    }
//    if(!this->lock_robot_connection(false)) return false;
//    bool result=false;
//    try{
//        double max_width=this->m_panda_hand->readOnce().max_width;
//        if(width==-1){
//            width=max_width;
//        }else{
//            if(width<0 || width>max_width){
//                spdlog::error("Gripper cannot reach width of "+std::to_string(width)+". Must be between 0 and "+std::to_string(max_width)+".");
//                this->unlock_robot_connection();
//                return false;
//            }
//        }
//        result=this->m_panda_hand->move(width,speed);
//        nlohmann::json p;
//        p["grasped_object"]="none";
//        this->_percept.mios_state.grasped_object="none";
//        this->_kb.get_local_memory()->modify_hidden_config_user(p);
//        this->m_panda_body->setLoad(0,{0,0,0},{0,0,0,0,0,0,0,0,0});
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//        result=false;
//    }
//    Eigen::Matrix<double,4,4> EE_T_TCP;
//    EE_T_TCP<<1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1;
//    nlohmann::json p;
//    msrm_utils::write_json_array<double,4,4>(p["EE_T_TCP"],EE_T_TCP);
//    this->get_kb()->get_local_memory()->get_persistent_data()->EE_T_TCP=EE_T_TCP;
//    if(!this->set_ee()){
//        result=false;
//    }
//    this->unlock_robot_connection();
//    return result;
//}

//void Core::gripper_grasp(double width, double speed, double force, double epsilon_inner, double epsilon_outer){
//    if(!this->_flag_gripper_connected){
//        spdlog::error("Gripper not connected.");
//        return;
//    }
//    try{
//        this->m_panda_hand->grasp(width,speed,force,epsilon_inner,epsilon_outer);
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//    }
//    this->_flag_gripper_busy=false;
//}

//void Core::gripper_move(double width, double speed){
//    if(!this->_flag_gripper_connected){
//        spdlog::error("Gripper not connected.");
//        return;
//    }
//    try{
//        this->m_panda_hand->move(width,speed);
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//    }
//    this->_flag_gripper_busy=false;
//}

//void Core::gripper_homing(){
//    if(!this->_flag_gripper_connected){
//        spdlog::error("Gripper not connected.");
//        return;
//    }
//    try{
//        this->m_panda_hand->homing();
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//    }
//    this->_flag_gripper_busy=false;
//}

//bool Core::is_grasping() const{
//    if(!this->_flag_gripper_connected){
//        spdlog::error("Gripper not connected.");
//        return false;
//    }
//    try{
//        return this->m_panda_hand->readOnce().is_grasped;
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//        return false;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//        return false;
//    }catch(franka::InvalidOperationException& e){
//        std::cout<<e.what()<<std::endl;
//        return false;
//    }
//    return true;
//}

//void Core::gripper_stop(){
//    if(!this->_flag_gripper_connected){
//        spdlog::error("Gripper not connected.");
//        return;
//    }
//    try{
//        this->m_panda_hand->stop();
//    }catch(franka::CommandException& e){
//        std::cout<<e.what()<<std::endl;
//    }catch(franka::NetworkException& e){
//        std::cout<<e.what()<<std::endl;
//    }
//    this->_flag_gripper_busy=false;
//}

bool Core::refresh_percept(std::optional<Eigen::Matrix<double,3,3> > O_R_TF){
    franka::RobotState robot_state;
    franka::GripperState gripper_state;
    if(!m_panda_body.get_robot_state(robot_state)){
        return false;
    }
    if(!m_panda_body.get_gripper_state(gripper_state)){
        return false;
    }
    m_percept.update(m_panda_body.get_panda_model(),robot_state,gripper_state,O_R_TF);
    return true;
}

const Percept& Core::get_percept() const{
    return m_percept;
}

//void Core::check_cartesian_velocity_workspace(Eigen::Matrix<double, 6, 1> &TF_dX_d, const Percept& p){
//    Eigen::Matrix<double,6,1> VC_dX_d = msrm_utils::rotate_vector(TF_dX_d,msrm_utils::invert_transformation_matrix(this->get_kb()->get_local_memory()->access_config_frames().O_T_VC));
//    Eigen::Matrix<double,3,1> VC_x = msrm_utils::invert_transformation_matrix(this->get_kb()->get_local_memory()->access_config_frames().O_T_VC).block<3,3>(0,0)*p.TF_T_EE.block<3,1>(0,3);
//    bool stop=false;
//    this->event["wall_hit_O"]={false,false,false,false,false,false};
//    double wall_distance=0.01;
//    Eigen::Matrix<double,3,1> wall_hit_O_lower, wall_hit_O_upper, wall_hit_EE_lower, wall_hit_EE_upper;
//    for(unsigned i=0;i<3;i++){
//        double diff_lower = VC_x(i)-this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i);
//        double wall_level_lower=1-diff_lower/wall_distance;
//        if(wall_level_lower>1)wall_level_lower=1;
//        if(wall_level_lower<0)wall_level_lower=0;
//        this->event["wall_hit_O"][2*i]=wall_level_lower;
//        wall_hit_O_lower(i)=wall_level_lower;
//        if(VC_x(i)<=this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i) && VC_dX_d(i)<0){
//            VC_dX_d(i)=0;
//        }
//        double diff_upper = this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i+1)-VC_x(i);
//        double wall_level_upper=1-diff_upper/wall_distance;
//        if(wall_level_upper>1)wall_level_upper=1;
//        if(wall_level_upper<0)wall_level_upper=0;
//        this->event["wall_hit_O"][2*i+1]=wall_level_upper;
//        if(VC_x(i)>=this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i+1) && VC_dX_d(i)>0){
//            VC_dX_d(i)=0;
//        }
//        wall_hit_O_upper(i)=wall_level_upper;
//    }
//    wall_hit_EE_lower=p.TF_T_EE.block<3,3>(0,0).transpose()*wall_hit_O_lower;
//    wall_hit_EE_upper=p.TF_T_EE.block<3,3>(0,0).transpose()*wall_hit_O_upper;
//    Eigen::Matrix<double,6,1> wall_hit_EE;
//    wall_hit_EE<<wall_hit_EE_lower(0),wall_hit_EE_upper(0),wall_hit_EE_lower(1),wall_hit_EE_upper(1),wall_hit_EE_lower(2),wall_hit_EE_upper(2);
//    for(unsigned i=0;i<6;i++){
//        if(wall_hit_EE(i)>1)wall_hit_EE(i)=1;
//        if(wall_hit_EE(i)<0)wall_hit_EE(i)=0;
//    }
//    msrm_utils::write_json_array<double,6,1>(this->event["wall_hit_EE"],wall_hit_EE);
//    TF_dX_d=msrm_utils::rotate_vector(VC_dX_d,this->get_kb()->get_local_memory()->access_config_frames().O_T_VC);
//}


//void Core::base_avoidance(Eigen::Matrix<double, 6, 1> &TF_dX_d, const Percept &p){
//    Eigen::Vector3d cp1,cp2,p_ee;
//    cp1<<0,0,0;
//    cp2<<0,0,0.5;
//    p_ee<<p.O_T_EE(0,3),p.O_T_EE(1,3),p.O_T_EE(2,3);
//    msrm_utils::Cylinder base_cylinder(this->get_kb()->get_local_memory()->access_config_user().base_cylinder_p1,
//                                       this->get_kb()->get_local_memory()->access_config_user().base_cylinder_p2,
//                                       this->get_kb()->get_local_memory()->access_config_user().base_cylinder_radius);
//    if(base_cylinder.contains(p_ee)){
//        Eigen::Matrix<double,3,3> O_R_Cyl = base_cylinder.get_frame(p_ee);
//        Eigen::Matrix<double,6,1> Cyl_dX_d = msrm_utils::rotate_vector(TF_dX_d,msrm_utils::invert_matrix(O_R_Cyl));
//        if(Cyl_dX_d(0)<0){
//            Cyl_dX_d(0)=0.01;
//        }
//        TF_dX_d=msrm_utils::rotate_vector(Cyl_dX_d,O_R_Cyl);
//    }
//}

void Core::dummy_control(std::function<franka::Torques (const franka::RobotState &)> control_cycle){
    franka::Torques tau_J={0,0,0,0,0,0,0};
    franka::RobotState state;
    state.K_F_ext_hat_K={0,0,0,0,0,0};
    state.O_F_ext_hat_K={0,0,0,0,0,0};
    state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    state.q={0,0,0,0,0,0,0};
    state.dq={0,0,0,0,0,0,0};
    while(!tau_J.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J=control_cycle(state);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void Core::dummy_control(std::function<franka::CartesianVelocities (const franka::RobotState &)> control_cycle){
    franka::CartesianVelocities dX_d={0,0,0,0,0,0};
    franka::RobotState state;
    while(!dX_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        dX_d=control_cycle(state);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void Core::dummy_control(std::function<franka::JointVelocities (const franka::RobotState &)> control_cycle){
    franka::JointVelocities dq_d={0,0,0,0,0,0,0};
    franka::RobotState state;
    while(!dq_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        dq_d=control_cycle(state);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

std::tuple<std::string,std::string,std::string> Core::get_desk_data(){
    return std::tie(this->_kb.get_local_memory()->access_config_system().ip_robot,
                    this->_kb.get_local_memory()->access_config_system().desk_name,
                    this->_kb.get_local_memory()->access_config_system().desk_pwd);
}

}

