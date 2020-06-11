#include "memory/lt_memory.hpp"
#include "task/task.hpp"
#include "task/taskfactory.hpp"
#include <spdlog/spdlog.h>
#include <msrm_utils/json.hpp>


namespace mios {

LTMemory::LTMemory():m_mongodb_client("mios"){
}

bool LTMemory::is_ok() const{
    if(!m_mongodb_client.health_check()){
        spdlog::error("Database health check failed.");
        return false;
    }
    return true;
}

void LTMemory::link_to_st_memory(STMemory *st_memory){
    m_st_memory=st_memory;
}

bool LTMemory::initialize(){
    spdlog::info("Initializing long-term memory...");
    if(!make_database_consistent()){
        return false;
    }else{
        return true;
    }
}

bool LTMemory::make_database_consistent(){
    nlohmann::json default_values;
    default_values=SystemParameters().to_json();
    default_values["name"]="system";
    if(!m_mongodb_client.make_document_consistent("system","parameters",default_values)){
        return false;
    }
    default_values=SafetyParameters().to_json();
    default_values["name"]="safety";
    if(!m_mongodb_client.make_document_consistent("safety","parameters",default_values)){
        return false;
    }
    default_values=ControlParameters().to_json();
    default_values["name"]="control";
    if(!m_mongodb_client.make_document_consistent("control","parameters",default_values)){
        return false;
    }
    default_values=LimitParameters().to_json();
    default_values["name"]="limits";
    if(!m_mongodb_client.make_document_consistent("limits","parameters",default_values)){
        return false;
    }
    default_values=FramesParameters().to_json();
    default_values["name"]="frames";
    if(!m_mongodb_client.make_document_consistent("frames","parameters",default_values)){
        return false;
    }
    default_values=UserParameters().to_json();
    default_values["name"]="user";
    if(!m_mongodb_client.make_document_consistent("user","parameters",default_values)){
        return false;
    }
    if(!make_default_skills_consistent()){
        return false;
    }
    if(!make_default_tasks_consistent()){
        return false;
    }
    if(!make_default_environment_consistent()){
        return false;
    }
    if(!m_mongodb_client.health_check()){
        spdlog::error("Could not check database health.");
        return false;
    }
    return true;
}

bool LTMemory::make_default_skills_consistent(){
    nlohmann::json default_values;
    default_values["name"]="TestSkill1";
    default_values["skill"]="";
    default_values["run_time"]=0;
    default_values["success"]=false;
    default_values["t_exception"]=0;
    default_values["cost_suc"]=0;
    default_values["cost_err"]=0;
    default_values["exception"]="none";
    default_values["mp_sequence"]={};
    if(!m_mongodb_client.make_document_consistent("TestSkill1","skills",default_values)){
        return false;
    }

    default_values.clear();
    default_values["name"]="HoldPose";
    default_values["t_max"]=0;
    if(!m_mongodb_client.make_document_consistent("HoldPose","skills",default_values)){
        return false;
    }

    default_values.clear();
    default_values["name"]="GenericWiggleMotion";
    default_values["dX_fourier_a_a"]={0,0,0,0,0,0};
    default_values["dX_fourier_b_a"]={0,0,0,0,0,0};
    default_values["dX_fourier_a_f"]={0,0,0,0,0,0};
    default_values["dX_fourier_b_f"]={0,0,0,0,0,0};
    default_values["dX_fourier_a_phi"]={0,0,0,0,0,0};
    default_values["dX_fourier_b_phi"]={0,0,0,0,0,0};
    default_values["use_EE"]=true;
    default_values["tap_to_finish"]=false;
    if(!m_mongodb_client.make_document_consistent("GenericWiggleMotion","skills",default_values)){
        return false;
    }

    default_values.clear();
    default_values["name"]="MoveToPoseJoint";
    default_values["speed"]={0};
    default_values["acc"]={0};
    default_values["q_g"]={0,0,0,0,0,0,0};
    default_values["t_q_g_offset"]={0,0,0,0,0,0,0};
    if(!m_mongodb_client.make_document_consistent("MoveToPoseJoint","skills",default_values)){
        return false;
    }
    return true;
}

bool LTMemory::make_default_tasks_consistent(){
    nlohmann::json default_values;
    default_values["name"]="TestTask1";
    default_values["skills"]={
    {"t1_s1",{
    {"type","TestSkill1"},
    {"skill",{
    {"objects",{{"object","TestObject1"}}}
}
},
    {"control",{{"control_mode",0}}}
},
},
    {"t1_s2",{
    {"type","TestSkill1"},
    {"skill",{
    {"objects",{{"object","TestObject1"}}}
}
},
    {"control",{{"control_mode",0}}}
},
}
};
    default_values["parameters"]={
    {"a",{0,0,0}},
    {"b",false},
    {"success",false},
    {"exception","none"},
    {"skill_test",0},
    {"queue_number",0},
    {"mp_sequence",{}}
};
    if(!m_mongodb_client.make_document_consistent("TestTask1","tasks",default_values)){
        return false;
    }

    default_values.clear();
    default_values["name"]="TestTask2";
    default_values["skills"]={
    {"t2_s1",{
    {"type","TestSkill1"},
    {"skill",{
    {"objects",{{"object","TestObject1"}}}
}
},
    {"control",{{"control_mode",0}}}
},
},
    {"t2_s2",{
    {"type","TestSkill1"},
    {"skill",{
    {"objects",{{"object","TestObject1"}}}
}
},
    {"control",{{"control_mode",0}}}
},
}
};
    default_values["parameters"]={
    {"d",{0,0}},
    {"e",0},
    {"f",false},
    {"stop_level",0},
    {"success",false}
};
    if(!m_mongodb_client.make_document_consistent("TestTask2","tasks",default_values)){
        return false;
    }

    default_values.clear();
    default_values["name"]="TestTask3";
    default_values["skills"]={
    {"t3_s1",{
    {"type","TestSkill1"},
    {"skill",{
    {"objects",{{"object","TestObject1"}}}
}
},
    {"control",{{"control_mode",0}}}
},
},
    {"t3_s2",{
    {"type","TestSkill1"},
    {"skill",{
    {"objects",{{"object","TestObject1"}}}
}
},
    {"control",{{"control_mode",0}}}
},
},
    {"t3_s3",{
    {"type","TestSkill1"},
    {"skill",{
    {"objects",{{"object","TestObject1"}}}
}
},
    {"control",{{"control_mode",0}}}
},
}
};
    default_values["parameters"]={
    {"g",{0,0,0,0}},
    {"h",false},
    {"i",0},
    {"j",""},
    {"stop_level",0},
    {"success",false}
};
    if(!m_mongodb_client.make_document_consistent("TestTask3","tasks",default_values)){
        return false;
    }


    default_values.clear();
    default_values["name"]="IdleTask";
    default_values["skills"]={
    {"sleep",{
    {"type","GenericWiggleMotion"},
},
},
    {"hold",{
    {"type","HoldPose"},
},},
    {"move",{
    {"type","MoveToPoseJoint"},
},}
};
    default_values["parameters"]={
    {"idle_mode","none"},
};
    if(!m_mongodb_client.make_document_consistent("IdleTask","tasks",default_values)){
        return false;
    }

    return true;
}

bool LTMemory::make_default_environment_consistent(){
    nlohmann::json default_values;
    Object o = Object("TestObject1");
    o.grasp_force=1;
    if(!m_mongodb_client.make_document_consistent("TestObject1","environment",o.to_json())){
        return false;
    }
    return true;
}

bool LTMemory::get_task_data(const std::string uuid, TaskData &data) const{
    if(m_task_data.find(uuid)==m_task_data.end()){
        return false;
    }else{
        data=m_task_data.at(uuid);
        return true;
    }
}

std::shared_ptr<Task> LTMemory::load_task(const std::string& task_id, const nlohmann::json& user_context,Core* core){
    std::shared_ptr<Task> task = TaskFactory::create_task(TaskFactory::get_task_name(task_id),core);
    if(!task->load_context(user_context)){
        spdlog::error("Could not load context for task " + task->get_id());
        return TaskFactory::create_task(TaskName::TaskNameNullTask,core);
    }
    if(task->get_context().find("parameters")!=task->get_context().end()){
        if(!task->read_parameters(task->get_context()["parameters"])){
            spdlog::error("Could not read parameters for task " + task->get_id());
            return TaskFactory::create_task(TaskName::TaskNameNullTask,core);
        }
    }
    return task;
}

std::shared_ptr<Task> LTMemory::load_subtask(const std::string& task_id, const nlohmann::json& user_context,Core* core){
    std::shared_ptr<Task> task = TaskFactory::create_task(TaskFactory::get_task_name(task_id),core);
    if(!task->load_context(user_context)){
        spdlog::error("Could not load context for subtask " + task->get_id());
        return TaskFactory::create_task(TaskName::TaskNameNullTask,core);
    }
    if(task->get_context().find("parameters")!=task->get_context().end()){
        if(!task->read_parameters(task->get_context()["parameters"])){
            spdlog::error("Could not read parameters for subtask " + task->get_id());
            return TaskFactory::create_task(TaskName::TaskNameNullTask,core);
        }
    }
    m_st_memory->put_subtask(task_id,task->get_context());
    return task;
}

bool LTMemory::load_default_parameters(nlohmann::json &parameters){
    if(!m_mongodb_client.read_document("control","parameters",parameters["control"])){
        return false;
    }
    if(!m_mongodb_client.read_document("frames","parameters",parameters["frames"])){
        return false;
    }
    if(!m_mongodb_client.read_document("safety","parameters",parameters["safety"])){
        return false;
    }
    if(!m_mongodb_client.read_document("system","parameters",parameters["system"])){
        return false;
    }
    if(!m_mongodb_client.read_document("user","parameters",parameters["user"])){
        return false;
    }
    if(!m_mongodb_client.read_document("limits","parameters",parameters["limits"])){
        return false;
    }
    return true;
}

bool LTMemory::load_default_task_context(const std::string task_id,nlohmann::json& task_context){
    return m_mongodb_client.read_document(task_id,"tasks",task_context);
}

bool LTMemory::load_default_skill_context(const std::string skill_type,nlohmann::json& skill_context){
    bool result = m_mongodb_client.read_document(skill_type,"skills",skill_context);
    nlohmann::json parameters = SkillParameters::get_default_values();
    for(const auto& param : parameters.items()){
        skill_context[param.key()]=param.value();
    }
    return result;
}

void LTMemory::store_task_data(const std::string &uuid, const std::string &task_id, const nlohmann::json &context, const TaskResult &result){
    m_task_data.emplace(std::make_pair(uuid,TaskData(task_id,context,result)));
}

bool LTMemory::load_environment(std::unordered_map<std::string, Object> &environment){
    std::set<nlohmann::json> docs;
    environment.emplace(std::make_pair("NullObject",Object("NullObject")));
    if(!m_mongodb_client.read_documents("environment",docs)){
        return false;
    }
    for(const auto& d: docs){
        environment.emplace(std::make_pair(d["name"],Object::from_json(d)));
    }
    return true;
}

bool LTMemory::upload_environment_element(const Object& element){
    return m_mongodb_client.write_document(element.name,"environment",element.to_json(),true);
}

bool LTMemory::update_database(){
    if(!m_mongodb_client.write_document("system","parameters",m_st_memory->read_parameters()->system.to_json(),true)){
        return false;
    }
    if(!m_mongodb_client.write_document("user","parameters",m_st_memory->read_parameters()->user.to_json(),true)){
        return false;
    }
    if(!m_mongodb_client.write_document("frames","parameters",m_st_memory->read_parameters()->frames.to_json(),true)){
        return false;
    }
    if(!m_mongodb_client.write_document("control","parameters",m_st_memory->read_parameters()->control.to_json(),true)){
        return false;
    }
    if(!m_mongodb_client.write_document("safety","parameters",m_st_memory->read_parameters()->safety.to_json(),true)){
        return false;
    }
    return true;
}

}
