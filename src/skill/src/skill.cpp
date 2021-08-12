#include "mios/skill/skill.hpp"

#include "mios/utils/exceptions.hpp"
#include "mios/data_structures/object.hpp"

#include "msrm_cpp_utils/files/files.hpp"
#include "msrm_cpp_utils/math/math.hpp"
#include "msrm_cpp_utils/json/json.hpp"
#include "msrm_cpp_utils/benchmarking/benchmarking.hpp"
#include "spdlog/spdlog.h"
#include "franka/exception.h"

#include <chrono>
#include "boost/filesystem.hpp"

namespace mios {

Skill::Skill(const std::string &type, const std::unordered_set<std::string> &objects, const std::string& id, Memory *memory, Portal* portal,std::set<ControlMode> control_modes):
    m_memory(memory),m_portal(portal),m_active_mp(std::make_shared<ManipulationPrimitive>("NullPrimitive",Percept(),memory)),m_control_modes(control_modes),m_life_cycle(SkillLifeCycle::slInit),
    m_flag_invoke_failure(false),m_flag_invoke_success(false),m_flag_pause(false),m_flag_parallels_running(false),m_stop_factor(1.0),m_type(type),m_id(id),m_objects(objects),
    m_msg_local_success(false),m_msg_global_success(false),m_cost_contact_forces_sum(0),m_cost_effort_avg_sum(0){
    spdlog::trace("Skill::Skill()");
    m_costs.insert(std::make_pair("ExecutionTime",0));
}

Skill::~Skill(){
    spdlog::trace("Skill::~Skill()");
    terminate_parallels();
}

std::shared_ptr<ManipulationPrimitive> Skill::get_mp(const std::string &mp) const{
    if(m_mp_graph.find(mp)==m_mp_graph.end()){
        spdlog::error("No MP with id "+mp+" is contained within skill of type "+m_type+". Check the skill implementation.");
        throw SkillException();
    }
    return m_mp_graph.at(mp);
}

std::shared_ptr<ManipulationPrimitive> Skill::create_mp(const std::string &name, const Percept &p){
    spdlog::trace("Skill::create_mp");
    if(m_active_mp->get_name()==name){
        spdlog::error("Manipulation primitive with name " + name + " is already active. Implementation of manipulation graph seems faulty.");
        throw SkillException();
    }
    return std::make_shared<ManipulationPrimitive>(name,p,m_memory);
}

Eigen::Matrix<double,4,4> Skill::get_object_pose_O(const std::string &object_name) const{
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        spdlog::error("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
        throw SkillException();
    }
    return m_grounded_objects.at(object_name).O_T_OB;
}

Eigen::Matrix<double,4,4> Skill::get_object_pose_T(const std::string &object_name) const{
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        spdlog::error("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
        throw SkillException();
    }
    return msrm_utils::rotate_matrix(m_grounded_objects.at(object_name).O_T_OB,m_memory->read_parameters()->frames.O_R_T.transpose());
}

Eigen::Matrix<double,4,4> Skill::get_object_grasp_pose_T(const std::string &object_name) const{
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        spdlog::error("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
        throw SkillException();
    }
    return msrm_utils::rotate_matrix(m_grounded_objects.at(object_name).O_T_OB*m_grounded_objects.at(object_name).OB_T_gp,m_memory->read_parameters()->frames.O_R_T.transpose());
}

Eigen::Matrix<double,4,4> Skill::get_object_grasp_pose_O(const std::string &object_name) const{
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        spdlog::error("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
        throw SkillException();
    }
    return m_grounded_objects.at(object_name).O_T_OB*m_grounded_objects.at(object_name).OB_T_gp;
}

const Object* Skill::get_object(const std::string &o) const{
    if(m_grounded_objects.find(o)==m_grounded_objects.end()){
        spdlog::error("Skill "+ this->get_id() +" of type "+m_type+" has no groundables with name " + o + ".");
        throw SkillException();
    }
    return &m_grounded_objects.at(o);
}

Object* Skill::update_object(const std::string &o){
    if(m_grounded_objects.find(o)==m_grounded_objects.end()){
        spdlog::error("Skill "+ this->get_id() +" of type "+m_type+" has no groundables with name " + o + ".");
        throw SkillException();
    }
    return &m_grounded_objects.at(o);
}

bool Skill::initialize([[maybe_unused]] const Percept &p){
    spdlog::trace("Skill::initialize");
    if(!msrm_utils::is_orthonormal(m_memory->read_parameters()->frames.O_R_T)){
        spdlog::error("O_R_T of skill "+m_id+" is invalid. Aborting execution.");
        std::cout<<"O_R_T: "<<m_memory->read_parameters()->frames.O_R_T<<std::endl;
        return false;
    }
    for(const auto& o : m_objects){
        if(m_grounded_objects.find(o)==m_grounded_objects.end()){
            spdlog::error("Object type " + o + " has not been grounded.");
            return false;
        }
    }
    return true;
}

Actuator* Skill::cycle(const Percept &p){
    m_result.p_1=p;
    Actuator* cmd;
    std::optional<std::shared_ptr<ManipulationPrimitive> > next_mp;

    if(m_life_cycle==SkillLifeCycle::slInit){
        spdlog::trace("Skill::cycle.init");
        m_active_mp=get_initial_mp(p);
        if(!m_active_mp->has_strategies()){
            spdlog::error("Manipulation primitive " + next_mp.value()->get_name() + " has no strategies.");
            throw SkillException();
        }
        m_result.p_0=p;
        m_time_start=std::chrono::high_resolution_clock::now();
        m_memory->get_live_context()->t_skill=std::chrono::high_resolution_clock::now();
        m_result.percepts.emplace(std::make_pair(m_active_mp->get_name(),p));
        m_result.cost=measure_cost(p);
        m_result.heuristic=get_goal_heuristic(p);
        if(!this->check_local_pre_conditions(p)){
            spdlog::error("Preconditions are not fulfilled.");
            m_stop_factor=0.1;
            cmd=m_active_mp->stop(p,m_stop_factor);
            m_life_cycle=SkillLifeCycle::slTerminate;
        }else{
            cmd=m_active_mp->initialize(p);
            m_flag_parallels_running=true;
            m_thr_parallels=std::thread(&Skill::run_parallels,this);
            m_life_cycle=SkillLifeCycle::slExecution;
        }
        return cmd;
    }
    if(m_life_cycle==SkillLifeCycle::slSettle){
        spdlog::trace("Skill::cycle.settle");
        if(m_active_mp->is_settled(m_memory->read_parameters()->skill->ignore_settling) && is_settled(p,m_memory->read_parameters()->skill->ignore_settling)){
            m_life_cycle=SkillLifeCycle::slTerminate;
        }
        return m_active_mp->stop(p,m_stop_factor);
    }
    if(m_life_cycle==SkillLifeCycle::slTerminate){
        spdlog::trace("Skill::cycle.terminate");
        stop_parallels();
        m_active_mp->terminate(p);
        cmd=m_active_mp->stop(p,m_stop_factor);
        cmd->stop();
        m_result.p_1=p;
        return cmd;
    }

    if(check_global_suc_conditions(p)){
        if(!m_msg_global_success){
            spdlog::info("Global success conditions of skill" + m_id + " have been triggered.");
            m_msg_global_success=true;
        }
        m_result.success=true;
    }
    if(check_local_suc_conditions(p)){
        if(!m_msg_local_success){
            spdlog::info("Local success conditions of skill " + m_id + " have been triggered.");
            m_msg_local_success=true;
        }
        m_result.success=true;
    }
    if(m_result.success && check_local_ex_conditions(p)){
        spdlog::info("Local exit conditions of skill " + m_id + " have been triggered.");
        m_life_cycle=SkillLifeCycle::slSettle;
        m_stop_factor=0.1;
        return m_active_mp->stop(p,m_stop_factor);
    }
    if(check_global_err_conditions(p)){
        spdlog::error("Global error conditions of skill " + m_id + " have been triggered.");
        m_result.success=false;
        m_life_cycle=SkillLifeCycle::slSettle;
        m_stop_factor=0.1;
        return m_active_mp->stop(p,m_stop_factor);
    }
    if(check_local_err_conditions(p)){
        spdlog::error("Local error conditions of skill " + m_id + " have been triggered.");
        m_result.success=false;
        m_life_cycle=SkillLifeCycle::slSettle;
        m_stop_factor=0.1;
        return m_active_mp->stop(p,m_stop_factor);
    }
    next_mp=graph_transition(p);
    if(next_mp.has_value()){
        if(!next_mp.value()->has_strategies()){
            spdlog::error("Manipulation primitive " + next_mp.value()->get_name() + " has no strategies.");
            throw SkillException();
        }
        m_life_cycle=SkillLifeCycle::slTransition;
    }

    if(m_life_cycle==SkillLifeCycle::slTransition){
        spdlog::trace("Skill::cycle.transition");
        Actuator blend_cmd=*(m_active_mp->cmd_from_buffer());
        m_active_mp->terminate(p);
        m_active_mp=next_mp.value();
        m_result.percepts.emplace(std::make_pair(m_active_mp->get_name(),p));
        m_life_cycle=SkillLifeCycle::slExecution;
        return m_active_mp->initialize(p,blend_cmd);
    }

    if(m_life_cycle==SkillLifeCycle::slExecution){
        auxiliaries(p);
        update_internal_models(p);
        update_policies(p);
        m_result.cost=measure_cost(p);
        m_result.heuristic=get_goal_heuristic(p);
        return m_active_mp->step(p);
    }
    spdlog::critical("Skill life cycle is undefined");
    m_result.success=false;
    m_result.exception=true;
    m_life_cycle=SkillLifeCycle::slSettle;
    m_stop_factor=1;
    return m_active_mp->stop(p);
}

bool Skill::is_settled(const Percept &p, bool ignore){
    if(ignore){
        return true;
    }
    if(p.proprioception.dq.norm()<m_memory->read_parameters()->user.env_dq &&
            p.proprioception.TF_dX_EE.block<3,1>(0,0).norm()<m_memory->read_parameters()->user.env_dX(0) &&
            p.proprioception.TF_dX_EE.block<3,1>(2,0).norm()<m_memory->read_parameters()->user.env_dX(1)){
        return true;
    }else{
        return false;
    }
}

void Skill::set_pause(bool pause){
    spdlog::trace("Skill::set_pause");
    m_flag_pause=pause;
}

void Skill::append_error(const std::string& error){
    spdlog::trace("Skill::append_error");
    m_result.last_errors.emplace_back(error);
}

Eigen::Matrix<double,3,3> Skill::get_O_R_T_0([[maybe_unused]] const Percept &p) const{
    return m_memory->read_parameters()->frames.O_R_T;
}

void Skill::set_init_mp(const std::string& name){
    spdlog::trace("Skill::set_init_mp");
    if(m_mp_graph.find(name)==m_mp_graph.end()){
        spdlog::error("Error when setting initial mp. No mp with name " + name + " available.");
        throw SkillException();
    }
    m_active_mp=m_mp_graph[name];
}

void Skill::terminate(const Percept& p){
    spdlog::trace("Skill::terminate");
    for(auto& mp : m_mp_graph){
        mp.second->terminate(p);
    }
    write_custom_results(m_result.results);
}

void Skill::invoke_failure(){
    spdlog::trace("Skill::invoke_failure");
    m_flag_invoke_failure=true;
}

void Skill::invoke_success(){
    spdlog::trace("Skill::invoke_success");
    m_flag_invoke_success=true;
}

bool Skill::check_global_err_conditions(const Percept& p) const{
    for(unsigned i=0;i<3;i++){
        if(fabs(p.proprioception.TF_F_ext_K(i))>=m_memory->read_parameters()->user.F_ext_max(0)){
            spdlog::error("Skill "+m_id+" has violated the maximum allowed external cartesian forces.");
            std::cout<<"F_ext: "<<p.proprioception.TF_F_ext_K<<std::endl;
            return true;
        }
    }
    for(unsigned i=0;i<3;i++){
        if(fabs(p.proprioception.TF_F_ext_K(i+3))>=m_memory->read_parameters()->user.F_ext_max(1)){
            spdlog::error("Skill "+m_id+" has violated the maximum allowed external cartesian forces.");
            std::cout<<"F_ext: "<<p.proprioception.TF_F_ext_K<<std::endl;
            return true;
        }
    }
    for(unsigned i=0;i<7;i++){
        if(fabs(p.proprioception.tau_ext(i))>=m_memory->read_parameters()->user.tau_ext_max(i)){
            spdlog::error("Skill "+m_id+" has violated the maximum allowed external joint torques at joint "+std::to_string(i)+".");
            std::cout<<"tau_ext: "<<p.proprioception.tau_ext<<std::endl;
            return true;
        }
    }
    for(unsigned i=0;i<7;i++){
        if(fabs(p.proprioception.tau_ext(i))>=m_memory->read_parameters()->user.tau_ext_max(i)){
            spdlog::error("Skill "+m_id+" has violated the maximum external joint torques at joint "+std::to_string(i)+".");
            return true;
        }
    }
    double run_time = std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_time_start).count();
    if(run_time>m_memory->read_parameters()->skill->time_max*1000 && m_memory->read_parameters()->skill->time_max>0){
        spdlog::error("Skill "+m_id+" has violated the maximum time limit of "+std::to_string(m_memory->read_parameters()->skill->time_max)+" s.");
        return true;
    }
    if(m_flag_invoke_failure){
        spdlog::error("Failure has been invoked externally");
        return true;
    }
    return false;
}

bool Skill::check_global_suc_conditions([[maybe_unused]] const Percept &p) const{
    if(m_flag_invoke_success){
        spdlog::info("Success has been invoked externally");
        return true;
    }
    return false;
}

bool Skill::check_local_pre_conditions([[maybe_unused]] const Percept &p){
    return true;
}

bool Skill::check_local_err_conditions([[maybe_unused]] const Percept &p){
    return false;
}

bool Skill::check_local_ex_conditions([[maybe_unused]] const Percept &p){
    return true;
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Skill::graph_transition([[maybe_unused]] const Percept &p){
    return {};
}

const SkillResult &Skill::get_result() const{
    return m_result;
}

const std::string& Skill::get_type() const{
    return m_type;
}

const std::string& Skill::get_id() const{
    return m_id;
}

bool Skill::ground_objects(){
    spdlog::trace("Skill::ground_objects");
    for(const auto& o : m_objects){
        if(m_memory->get_parameters()->skill->objects.find(o)==m_memory->get_parameters()->skill->objects.end()){
            spdlog::error("No object of type " + o + " has been provided.");
            return false;
        }
    }
    for(const std::pair<std::string,std::string>& m : m_memory->get_parameters()->skill->objects){
        spdlog::debug("object_ungrounded: "+m.first + ", object_grounded: " + m.second);
        if(m_objects.find(m.first)==m_objects.end()){
            spdlog::error("Skill of type " + m_type + " does not use an object of type " + m.first +".");
            return false;
        }
        if(m_grounded_objects.find(m.first)!=m_grounded_objects.end()){
            spdlog::error("Skill " + m_id + " already has a grounded object of type " + m.first + ".");
            return false;
        }
        Object* o = m_memory->get_object(m.second);
        if(o->name=="NullObject"){
            spdlog::error("No object with name "+m.second+" exists.");
            return false;
        }
        m_grounded_objects.emplace(std::make_pair(m.first,*o));
    }
    return true;
}

bool Skill::modify_objects(){
    spdlog::trace("Skill::modify_objects");
    for(const auto& o : m_objects){
        if(m_memory->get_parameters()->skill->objects_modifier.find(o)==m_memory->get_parameters()->skill->objects_modifier.end()){
            continue;
        }else{
            nlohmann::json modifier = m_memory->get_parameters()->skill->objects_modifier[o];
            if(modifier.find("O_T_OB")!=modifier.end() && modifier.find("T_T_OB")!=modifier.end()){
                spdlog::error("Cannot modify O_T_OB and T_T_OB for object " + o + " for skill " + m_id + " at the same time.");
                return false;
            }
            if(modifier.find("O_T_OB")!=modifier.end()){
                Eigen::Matrix<double,4,4> O_T_OB_mod;
                if(!msrm_utils::read_json_param<double,4,4>(modifier["O_T_OB"],O_T_OB_mod)){
                    spdlog::error("Could not load object modifier for O_T_OB for object " + o + ".");
                    return false;
                }
                update_object(o)->O_T_OB.block<3,1>(0,3)+=O_T_OB_mod.block<3,1>(0,3);
                update_object(o)->O_T_OB.block<3,3>(0,0)=O_T_OB_mod.block<3,3>(0,0)*update_object(o)->O_T_OB.block<3,3>(0,0);
            }
            if(modifier.find("T_T_OB")!=modifier.end()){
                Eigen::Matrix<double,4,4> T_T_OB_mod;
                if(!msrm_utils::read_json_param<double,4,4>(modifier["T_T_OB"],T_T_OB_mod)){
                    spdlog::error("Could not load object modifier for T_T_OB for object " + o + ".");
                    return false;
                }
                update_object(o)->O_T_OB.block<3,1>(0,3)+=(m_memory->get_parameters()->frames.O_R_T*T_T_OB_mod.block<3,1>(0,3));
                update_object(o)->O_T_OB.block<3,3>(0,0)=msrm_utils::rotate_matrix(T_T_OB_mod,m_memory->get_parameters()->frames.O_R_T).block<3,3>(0,0)*update_object(o)->O_T_OB.block<3,3>(0,0);
            }
        }
    }
    return true;
}

void Skill::auxiliaries([[maybe_unused]] const Percept &p){

}

void Skill::parallels(){

}

void Skill::run_parallels(){
    spdlog::trace("Skill::run_parallels");
    while(m_flag_parallels_running){
        auto start = std::chrono::high_resolution_clock::now();
        this->parallels();
        auto finish = std::chrono::high_resolution_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(finish - start);
        double t_sleep_max = 1.0/m_memory->read_parameters()->skill->parallels_frequency;

        std::this_thread::sleep_for(std::chrono::microseconds(long(t_sleep_max*1000000-elapsed.count())));
    }
}

void Skill::stop_parallels(){
    spdlog::trace("Skill::stop_parallels");
    m_flag_parallels_running=false;
}

void Skill::terminate_parallels(){
    spdlog::trace("Skill::terminate_parallels");
    m_flag_parallels_running=false;
    if(m_thr_parallels.joinable()){
        m_thr_parallels.join();
    }
}

SkillCost Skill::measure_cost(const Percept &p){
    m_cost_contact_forces_sum += p.proprioception.K_F_ext_K.norm();
    m_cost_effort_avg_sum += p.proprioception.tau_j.norm();

    SkillCost cost;
    cost.time = std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_skill).count()/1000.0;
    cost.contact_forces = m_cost_contact_forces_sum / (std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_skill).count() + 1);
    cost.effort_avg = m_cost_effort_avg_sum / (std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_skill).count() +1);
    cost.effort_total += p.proprioception.tau_j.norm();
    cost.distance += p.proprioception.dq.norm()*0.001;
    cost.custom = get_custom_cost(p);
    return cost;
}

double Skill::get_custom_cost([[maybe_unused]] const Percept &p){
    return 0;
}

void Skill::write_custom_results([[maybe_unused]] nlohmann::json &custom_results){
    spdlog::trace("Skill::write_custom_results");
    m_result.results=nlohmann::json();
}

void Skill::write_logs(){
    spdlog::trace("Skill::write_logs");
    if(!m_memory->read_parameters()->skill->log_data || m_data_log.size()==0){
        return;
    }
    spdlog::info("Writing logs into file...");
    std::string log_file = boost::filesystem::path(boost::filesystem::current_path()).string()+"/../logs/logs_"+m_memory->read_parameters()->skill->log_name+".txt";
    boost::filesystem::create_directories(boost::filesystem::path(boost::filesystem::current_path()).string()+"/../logs/");
    std::remove(log_file.c_str());
    try{
        for(const auto& el : m_data_log[0].items()){
            if(m_data_log[0][el.key()].is_array()){
                for(unsigned i=0;i<m_data_log[0][el.key()].size();i++){
                    msrm_utils::write_data_to_file(el.key(),log_file);
                }
            }else{
                msrm_utils::write_data_to_file(el.key(),log_file);
            }
        }
        msrm_utils::write_endl_to_file(log_file);
        if(m_log_cnt>=m_data_log.size()){
            m_log_cnt=static_cast<unsigned long>(m_data_log.size());
        }
        for(unsigned i=0;i<m_log_cnt;i++){
            for(const auto& el : m_data_log[i].items()){
                if(m_data_log[i][el.key()].is_array()){
                    for(unsigned j=0;j<m_data_log[i][el.key()].size();j++){
                        msrm_utils::write_data_to_file(m_data_log[i][el.key()][j],log_file);
                    }
                }else{
                    msrm_utils::write_data_to_file(m_data_log[i][el.key()],log_file);
                }
            }
            msrm_utils::write_endl_to_file(log_file);
        }
    }catch(const nlohmann::json::exception& e){
        spdlog::debug(e.what());
    }
    spdlog::info("Logs have been written to "+log_file+".");
}

nlohmann::json& Skill::get_custom_results(){
    return m_result.results;
}

const std::set<ControlMode>* Skill::get_valid_control_modes() const{
    return &m_control_modes;
}

const std::shared_ptr<ManipulationPrimitive> Skill::get_active_mp() const{
    return m_active_mp;
}

void Skill::update_internal_models([[maybe_unused]] const Percept& p){

}

void Skill::update_policies([[maybe_unused]] const Percept &p){

}

double Skill::get_goal_heuristic([[maybe_unused]] const Percept &p){
    return 0;
}


bool Skill::is_in_env(const std::string &pose, const std::string &mp, const Percept &p){
    if(get_active_mp()->get_strategy_interface(mp)->finished()){
        if((p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T(pose).block<3,1>(0,3)).norm()<m_memory->read_parameters()->user.env_X(0)
           && acos(((get_object_pose_T(pose).block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2) < m_memory->read_parameters()->user.env_X(1)){
            return true;
        }else{
            return false;
        }
    }
    return false;
}

}
