#include "tasks/generic_task.hpp"
#include <msrm_utils/files.hpp>

#include "skills/test_skill_1.hpp"

namespace mios {

GenericTask::GenericTask(Core* core):Task("GenericTask",core){

}

void GenericTask::initialize_context(){
    for(const auto& s : m_skills){
        insert_skill(s.first,s.second);
    }
}

void GenericTask::execute(){
    for(unsigned i=0;i<m_skills.size();i++){
        execute_any_skill(i);
    }
}

void GenericTask::evaluate(){

}

void GenericTask::execute_any_skill(unsigned index){
    std::string name = m_skills[index].first;
    switch(msrm_utils::str_to_int(name.c_str())){
    case msrm_utils::str_to_int("TestSkill1"):
        execute_skill<TestSkill1,SkillParametersTestSkill1>(name);
        break;
    default:
        throw TaskException("Skill with name " + name + " not known to GenericTask");
    }
}

bool GenericTask::read_parameters(const nlohmann::json &params){
    std::vector<std::string> names;
    std::vector<std::string> types;
    m_skills.resize(0);

    if(!msrm_utils::read_json_param(params,"skill_names",names)){
        spdlog::error("Missing parameter: skill_names.");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"skill_types",types)){
        spdlog::error("Missing parameter: skill_types.");
        return false;
    }
    if(names.size()==0 || types.size()==0){
        spdlog::error("Generic task requires at least on skill.");
        return false;
    }
    if(names.size()!=types.size()){
        spdlog::error("Skill names and types must have same size.");
        return false;
    }
    for(unsigned i=0;i<names.size();i++){
        m_skills.emplace_back(std::make_pair(names[i],types[i]));
    }
    return true;
}

}
