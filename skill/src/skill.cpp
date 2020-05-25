#include "skill/skill.hpp"
#include <franka/exception.h>
#include <chrono>

#include "primitives/nullprimitive.hpp"
#include "skills/nullskill.hpp"
#include "utils/exceptions.hpp"
#include "data_structures/object.hpp"
#include <msrm_utils/math.hpp>
#include <spdlog/spdlog.h>

namespace mios {

Skill::Skill(const std::string &type, const std::unordered_set<std::string> &objects, const std::string& id, Memory *memory, const Percept &p):
    m_memory(memory),m_active_mp(std::make_shared<NullPrimitive>("NullPrimitive",p,std::make_shared<MPParametersNullPrimitive>(),std::make_shared<NullAttractor>(),memory)),m_life_cycle(SkillLifeCycle::slInit),
    m_flag_invoke_failure(false),m_flag_invoke_success(false),m_flag_pause(false),m_flag_parallels_running(false),m_type(type),m_id(id),m_objects(objects){
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

Eigen::Matrix<double,4,4> Skill::get_object_grasp_pose_T(const std::string &object_name){
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        throw SkillException("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
    }
    const Object* object=m_memory->get_object(object_name);
    return msrm_utils::rotate_matrix(object->O_T_OB*object->OB_T_gp,m_memory->read_parameters()->frames.O_R_T.transpose());
}

Eigen::Matrix<double,4,4> Skill::get_object_grasp_pose_O(const std::string &object_name){
    if(m_grounded_objects.find(object_name)==m_grounded_objects.end()){
        throw SkillException("No object of type "+object_name+" in skill "+ get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
    }
    const Object* object=m_memory->get_object(object_name);
    return object->O_T_OB*object->OB_T_gp;
}

const Object* Skill::get_object(const std::string &o) const{
    if(m_grounded_objects.find(o)==m_grounded_objects.end()){
        throw SkillException("No object of type "+o+" in skill "+ this->get_id() +" of type "+m_type+" has been assigned. Check the task description or assign it manually in the task implementation.");
    }
    return m_grounded_objects.at(o);
}

void Skill::write_O_R_TF_to_config(const Percept &p){
    m_memory->get_parameters()->frames.O_R_T=get_O_R_T_0(p);
}

bool Skill::initialize(const Percept &p){
    if(!msrm_utils::is_orthonormal(m_memory->read_parameters()->frames.O_R_T)){
        msrm_utils::print_error("O_R_TF of skill "+m_id+" is invalid. Aborting execution.");
        std::cout<<"O_R_TF: "<<m_memory->read_parameters()->frames.O_R_T<<std::endl;
        return false;
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
            cmd=m_active_mp->stop(p);
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
        return m_active_mp->stop(p);
    }
    if(m_life_cycle==SkillLifeCycle::slTerminate){
        terminate_parallels();
        cmd=m_active_mp->stop(p);
        cmd->stop();
        m_result.p_1=p;
        return cmd;
    }

    if(check_global_suc_conditions(p)){
        spdlog::info("Global success conditions of skill" + m_id + " have been triggered.");
        m_result.success=true;
        m_life_cycle=SkillLifeCycle::slSettle;
        return m_active_mp->stop(p);
    }
    if(check_local_suc_conditions(p)){
        spdlog::info("Local success conditions of skill" + m_id + " have been triggered.");
        m_result.success=true;
    }
    if(check_local_ex_conditions(p) && m_result.success){
        spdlog::info("Local exit conditions of skill" + m_id + " have been triggered.");
        m_life_cycle=SkillLifeCycle::slSettle;
        return m_active_mp->stop(p);
    }
    if(check_global_err_conditions(p)){
        spdlog::error("Global error conditions of skill " + m_id + " have been triggered.");
        m_result.success=false;
        m_life_cycle=SkillLifeCycle::slSettle;
        return m_active_mp->stop(p);
    }
    if(check_local_err_conditions(p)){
        spdlog::error("Local error conditions of skill " + m_id + " have been triggered.");
        m_result.success=false;
        m_life_cycle=SkillLifeCycle::slSettle;
        return m_active_mp->stop(p);
    }
    next_mp=graph_transition(p);
    if(next_mp.has_value()){
        m_life_cycle=SkillLifeCycle::slTransition;
    }

    if(m_life_cycle==SkillLifeCycle::slTransition){
        Actuator blend_cmd=*(m_active_mp->cmd_from_buffer());
        m_active_mp=next_mp.value();
        m_result.percepts.emplace(std::make_pair(m_active_mp->get_name(),p));
        m_life_cycle=SkillLifeCycle::slExecution;
        return m_active_mp->initialize(p,blend_cmd);
    }

    if(m_life_cycle==SkillLifeCycle::slExecution){
        auxiliaries(p);
        return m_active_mp->step(p);
    }
    spdlog::critical("Skill life cycle is undefined");
    m_result.success=false;
    m_result.exception=true;
    m_life_cycle=SkillLifeCycle::slSettle;
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

void Skill::terminate(){
    for(auto& mp : m_mp_graph){
        mp.second->terminate();
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
    for(unsigned i=0;i<6;i++){
        if(fabs(p.proprioception.TF_F_ext_K(i))>=m_memory->read_parameters()->user.F_ext_max(i)){
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
    if(run_time>m_memory->read_parameters()->skill->common.time_max && m_memory->read_parameters()->skill->common.time_max>0){
        spdlog::error("Skill "+m_id+" has violated the maximum time limit of "+std::to_string(m_memory->read_parameters()->skill->common.time_max)+" s.");
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
    for(const std::pair<std::string,std::string>& m : m_memory->get_parameters()->skill->common.objects){
        if(m_objects.find(m.first)==m_objects.end()){
            spdlog::error("Skill of type " + m_type + " does not use an object of type " + m.first +".");
            return false;
        }
        if(m_grounded_objects.find(m.first)!=m_grounded_objects.end()){
            spdlog::error("Skill " + m_id + " already has a grounded object of type " + m.first + ".");
            return false;
        }
        const Object* o = m_memory->get_object(m.second);
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
        double t_sleep_max = 1.0/m_memory->read_parameters()->skill->common.parallels_frequency;

        std::this_thread::sleep_for(std::chrono::microseconds(long(t_sleep_max*1000000-elapsed.count())));
    }
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

const std::shared_ptr<ManipulationPrimitive> Skill::get_active_mp() const{
    return m_active_mp;
}

void Skill::write_costs(double cost_suc, double cost_err){
    m_result.cost_suc=cost_suc;
    m_result.cost_err=cost_err;
}

void Skill::evaluate(){

}

}
