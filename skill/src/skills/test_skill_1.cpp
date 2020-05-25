#include "skills/test_skill_1.hpp"

#include <spdlog/spdlog.h>
#include <franka/exception.h>

namespace mios{

bool SkillParametersTestSkill1::read_parameters(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param(parameters,"run_time",run_time)){
        msrm_utils::print_debug("Could not load parameter: run_time [double]");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"success",success)){
        success=false;
    }
    if(!msrm_utils::read_json_param(parameters,"t_exception",t_exception)){
        t_exception=0;
    }
    if(!msrm_utils::read_json_param(parameters,"exception",exception)){
        exception="none";
    }
    spdlog::debug("###############################   Skill parameters   ######################################");
    spdlog::debug("run_time: "+std::to_string(run_time));
    spdlog::debug("success: "+std::to_string(success));
    spdlog::debug("t_exception: "+std::to_string(t_exception));
    spdlog::debug("exception: "+exception);
    spdlog::debug("###########################################################################################");
    return true;
}

TestSkill1::TestSkill1(const std::string &name, Memory *memory, const Percept &p):Skill("TestSkill1",{"object"},name,memory,p){}

std::shared_ptr<ManipulationPrimitive> TestSkill1::get_initial_mp(const Percept &p_0){
    return create_mp<BasicPrimitive,MPParametersBasic,BasicAttractor>("mp",p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TestSkill1::graph_transition(const Percept& p){
    return {};
}

bool TestSkill1::check_local_suc_conditions(const Percept& p){
    std::shared_ptr<SkillParametersTestSkill1> c = get_parameters<SkillParametersTestSkill1>();
    double t_run=std::chrono::duration_cast<std::chrono::seconds>(p.time-m_memory->get_live_context()->t_skill).count();
    if(c->success && t_run>c->run_time){
        spdlog::debug("Local success condition triggered at "+std::to_string(t_run));
        return true;
    }else{
        return false;
    }
}

bool TestSkill1::check_local_err_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTestSkill1> c = get_parameters<SkillParametersTestSkill1>();
    double t_run=std::chrono::duration_cast<std::chrono::seconds>(p.time-m_memory->get_live_context()->t_skill).count();
    if(!c->success && t_run>c->run_time){
        spdlog::debug("Local error condition triggered at "+std::to_string(t_run));
        return true;
    }else{
        return false;
    }
}

Eigen::Matrix<double,3,3> TestSkill1::get_O_R_T_0(const Percept &p){
    spdlog::debug("get_O_R_T_0");
    Eigen::Matrix<double,3,3> R = get_object_grasp_pose_O("object").block<3,3>(0,0);
    return R;
}

void TestSkill1::auxiliaries(const Percept &p){
    std::shared_ptr<SkillParametersTestSkill1> c = get_parameters<SkillParametersTestSkill1>();
    double t_run=std::chrono::duration_cast<std::chrono::seconds>(p.time-m_memory->get_live_context()->t_skill).count();
    if(t_run>c->t_exception){
        if(c->exception=="control"){
            throw franka::ControlException("This is a control exception that has been thrown for test purposes");
        }
        if(c->exception=="invalid"){
            throw franka::InvalidOperationException("This is an invalid operation exception that has been thrown for test purposes");
        }
        if(c->exception=="network"){
            throw franka::NetworkException("This is a network exception that has been thrown for test purposes");
        }
        if(c->exception=="realtime"){
            throw franka::RealtimeException("This is a realtime exception that has been thrown for test purposes");
        }
        if(c->exception=="skill"){
            throw SkillException("This is a skill exception that has been thrown for test purposes");
        }
    }
}

void TestSkill1::evaluate(){
    msrm_utils::print_debug("Evaluate");
    std::shared_ptr<SkillParametersTestSkill1> c = get_parameters<SkillParametersTestSkill1>();
    get_custom_results()["exception"]=c->exception;
    get_custom_results()["run_time"]=c->run_time;
    get_custom_results()["success"]=c->success;
    get_custom_results()["t_exception"]=c->t_exception;
    if(m_memory->get_live_parameter("test_parameter_1").has_value()){
        get_custom_results()["test_parameter_1"]=m_memory->get_live_parameter("test_parameter_1").value();
    }
    if(m_memory->get_live_parameter("test_parameter_2").has_value()){
        get_custom_results()["test_parameter_1"]=m_memory->get_live_parameter("test_parameter_2").value();
    }
    if(m_memory->get_live_parameter("test_parameter_3").has_value()){
        get_custom_results()["test_parameter_1"]=m_memory->get_live_parameter("test_parameter_3").value();
    }
}

void TestSkill1::parallels(){
    double cnt;
    msrm_utils::read_json_param(get_custom_results(),"parallels_cnt",cnt);
    get_custom_results()["parallels_cnt"]=cnt+1;
}
}
