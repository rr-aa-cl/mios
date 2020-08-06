#include "skill/skill.hpp"
#include <franka/exception.h>
#include <chrono>

#include "skills/nullskill.hpp"
#include "utils/exceptions.hpp"
#include "data_structures/object.hpp"
#include <msrm_utils/math.hpp>
#include <msrm_utils/benchmarking.hpp>
#include <spdlog/spdlog.h>

namespace mios {

Skill::Skill(const std::string &type, const std::unordered_set<std::string> &objects, const std::string& id, Memory *memory, Portal* portal, const Percept &p,std::set<ControlMode> control_modes):
    m_memory(memory),m_portal(portal),m_active_mp(std::make_shared<ManipulationPrimitive>("NullPrimitive",p,memory)),m_control_modes(control_modes),m_life_cycle(SkillLifeCycle::slInit),
    m_flag_invoke_failure(false),m_flag_invoke_success(false),m_flag_pause(false),m_flag_parallels_running(false),m_stop_factor(1.0),m_type(type),m_id(id),m_objects(objects),
    m_msg_local_success(false),m_msg_global_success(false){
}

Skill::~Skill(){
    terminate_parallels();
}

std::shared_ptr<ManipulationPrimitive> Skill::get_mp(const std::string &mp) const{
    if(m_mp_graph.find(mp)==m_mp_graph.end()){
        throw SkillException("No MP with id "+mp+" is contained within skill of type "+m_type+". Check the skill implementation.");
    }
    return m_mp_graph.at(mp);
}

std::shared_ptr<ManipulationPrimitive> Skill::create_mp(const std::string &name, const Percept &p){
    if(m_active_mp->get_name()==name){
        throw SkillException("Manipulation primitive with name " + name + " is already active. Implementation of manipulation graph seems faulty.");
    }
    return std::make_shared<ManipulationPrimitive>(name,p,m_memory);
}

Eigen::Matrix<double,4,4> Skill::get_object_pose_O(const std::string &object_name) const{
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        throw SkillException("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
    }
    const Object* object=m_grounded_objects.at(object_name);
    return object->O_T_OB;
}

Eigen::Matrix<double,4,4> Skill::get_object_pose_T(const std::string &object_name) const{
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        throw SkillException("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
    }
    const Object* object=m_grounded_objects.at(object_name);
    return msrm_utils::rotate_matrix(object->O_T_OB,m_memory->read_parameters()->frames.O_R_T.transpose());
}

Eigen::Matrix<double,4,4> Skill::get_object_grasp_pose_T(const std::string &object_name) const{
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        throw SkillException("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
    }
    const Object* object=m_grounded_objects.at(object_name);
    return msrm_utils::rotate_matrix(object->O_T_OB*object->OB_T_gp,m_memory->read_parameters()->frames.O_R_T.transpose());
}

Eigen::Matrix<double,4,4> Skill::get_object_grasp_pose_O(const std::string &object_name) const{
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        throw SkillException("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
    }
    const Object* object=m_grounded_objects.at(object_name);
    return object->O_T_OB*object->OB_T_gp;
}

const Object* Skill::get_object(const std::string &o) const{
    if(m_grounded_objects.find(o)==m_grounded_objects.end()){
        throw SkillException("Skill "+ this->get_id() +" of type "+m_type+" has no groundables with name " + o + ".");
    }
    return m_grounded_objects.at(o);
}

Object* Skill::update_object(const std::string &o){
    if(m_grounded_objects.find(o)==m_grounded_objects.end()){
        throw SkillException("Skill "+ this->get_id() +" of type "+m_type+" has no groundables with name " + o + ".");
    }
    return m_grounded_objects.at(o);
}

bool Skill::initialize(const Percept &p){
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
        m_active_mp=get_initial_mp(p);
        m_result.p_0=p;
        m_memory->get_live_context()->t_skill=std::chrono::high_resolution_clock::now();
        m_result.percepts.emplace(std::make_pair(m_active_mp->get_name(),p));
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
        if(m_active_mp->is_settled()){
            m_life_cycle=SkillLifeCycle::slTerminate;
        }
        return m_active_mp->stop(p,m_stop_factor);
    }
    if(m_life_cycle==SkillLifeCycle::slTerminate){
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
        m_life_cycle=SkillLifeCycle::slTransition;
    }

    if(m_life_cycle==SkillLifeCycle::slTransition){
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
        return m_active_mp->step(p);
    }
    spdlog::critical("Skill life cycle is undefined");
    m_result.success=false;
    m_result.exception=true;
    m_life_cycle=SkillLifeCycle::slSettle;
    m_stop_factor=1;
    return m_active_mp->stop(p);
}

void Skill::set_pause(bool pause){
    m_flag_pause=pause;
}

void Skill::append_error(const std::string& error){
    m_result.last_errors.emplace_back(error);
}

Eigen::Matrix<double,3,3> Skill::get_O_R_T_0(const Percept &p) const{
    return m_memory->read_parameters()->frames.O_R_T;
}

void Skill::set_init_mp(const std::string& name){
    if(m_mp_graph.find(name)==m_mp_graph.end()){
        throw SkillException("Error when setting initial mp. No mp with name " + name + " available.");
    }
    m_active_mp=m_mp_graph[name];
}

void Skill::terminate(const Percept& p){
    for(auto& mp : m_mp_graph){
        mp.second->terminate(p);
    }
    this->evaluate();
}

void Skill::invoke_failure(){
    m_flag_invoke_failure=true;
}

void Skill::invoke_success(){
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
    double run_time = std::chrono::duration_cast<std::chrono::seconds>(p.time-m_time_start).count();
    if(run_time>m_memory->read_parameters()->skill->time_max && m_memory->read_parameters()->skill->time_max>0){
        spdlog::error("Skill "+m_id+" has violated the maximum time limit of "+std::to_string(m_memory->read_parameters()->skill->time_max)+" s.");
        return true;
    }
    if(m_flag_invoke_failure){
        spdlog::error("Failure has been invoked externally");
        return true;
    }
    return false;
}

bool Skill::check_global_suc_conditions(const Percept &p) const{
    if(m_flag_invoke_success){
        spdlog::info("Success has been invoked externally");
        return true;
    }
    return false;
}

bool Skill::check_local_pre_conditions(const Percept &p){
    return true;
}

bool Skill::check_local_err_conditions(const Percept &p){
    return false;
}

bool Skill::check_local_ex_conditions(const Percept &p){
    return true;
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Skill::graph_transition(const Percept &p){
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
    spdlog::debug("SKILL:GROUND_OBJECTS");
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
        if(o==nullptr){
            spdlog::error("No object with name "+m.second+" exists.");
            return false;
        }
        m_grounded_objects.emplace(std::make_pair(m.first,o));
    }
    return true;
}

void Skill::auxiliaries(const Percept &p){

}

void Skill::parallels(){

}

void Skill::run_parallels(){
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
    m_flag_parallels_running=false;
}

void Skill::terminate_parallels(){
    m_flag_parallels_running=false;
    if(m_thr_parallels.joinable()){
        m_thr_parallels.join();
    }
}

void Skill::write_custom_results(nlohmann::json results){
    m_result.results=results;
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

void Skill::write_costs(double cost_suc, double cost_err){
    m_result.cost_suc=cost_suc;
    m_result.cost_err=cost_err;
}

void Skill::evaluate(){

}

void Skill::update_internal_models(const Percept& p){

}

void Skill::update_policies(const Percept &p){

}

}
