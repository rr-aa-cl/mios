#include "tasks/generic_task.hpp"
#include <msrm_utils/files.hpp>

#include "skills/test_skill_1.hpp"
#include "skills/move_to_pose_cart.hpp"
#include "skills/move_to_pose_joint.hpp"
#include "skills/move_to_contact.hpp"
#include "skills/hand_guiding.hpp"
#include "skills/hold_pose.hpp"
#include "skills/generic_wiggle_motion.hpp"
#include "skills/telepresence.hpp"
#include "skills/push.hpp"
#include "skills/shove.hpp"
#include "skills/tip.hpp"
#include "skills/file.hpp"
#include "skills/extraction.hpp"
#include "skills/insertion.hpp"
#include "skills/wipe.hpp"

namespace mios {

GenericTask::GenericTask(Core* core):Task("GenericTask",core){

}

void GenericTask::initialize_context(){
    for(const auto& s : m_skills){
        insert_skill(s.first,s.second);
        reserve_skill(s.first);
    }
}

void GenericTask::execute(){
    for(unsigned i=0;i<m_skills.size();i++){
        execute_any_skill(i);
    }
}

void GenericTask::execute_any_skill(unsigned index){
    std::string name = m_skills[index].first;
    std::string type = m_skills[index].second;
    switch(msrm_utils::str_to_int(type.c_str())){
    case msrm_utils::str_to_int("TestSkill1"):
        execute_skill<TestSkill1,SkillParametersTestSkill1>(name);
        break;
    case msrm_utils::str_to_int("MoveToPoseJoint"):
        execute_skill<MoveToPoseJoint,SkillParametersMoveToPoseJoint>(name);
        break;
    case msrm_utils::str_to_int("MoveToPoseCart"):
        execute_skill<MoveToPoseCart,SkillParametersMoveToPoseCart>(name);
        break;
    case msrm_utils::str_to_int("MoveToContact"):
        execute_skill<MoveToContact,SkillParametersMoveToContact>(name);
        break;
    case msrm_utils::str_to_int("GenericWiggleMotion"):
        execute_skill<GenericWiggleMotion,SkillParametersGenericWiggleMotion>(name);
        break;
    case msrm_utils::str_to_int("HoldPose"):
        execute_skill<HoldPose,SkillParametersHoldPose>(name);
        break;
    case msrm_utils::str_to_int("HandGuiding"):
        execute_skill<HandGuiding,SkillParametersHandGuiding>(name);
        break;
    case msrm_utils::str_to_int("Telepresence"):
        execute_skill<Telepresence,SkillParametersTelepresence>(name);
        break;
    case msrm_utils::str_to_int("Push"):
        execute_skill<Push,SkillParametersPush>(name);
        break;
    case msrm_utils::str_to_int("Tip"):
        execute_skill<Tip,SkillParametersTip>(name);
        break;
    case msrm_utils::str_to_int("Shove"):
        execute_skill<Shove,SkillParametersShove>(name);
        break;
    case msrm_utils::str_to_int("File"):
        execute_skill<File,SkillParametersFile>(name);
        break;
    case msrm_utils::str_to_int("Extraction"):
        execute_skill<Extraction,SkillParametersExtraction>(name);
        break;
    case msrm_utils::str_to_int("Insertion"):
        execute_skill<Insertion,SkillParametersInsertion>(name);
        break;
    case msrm_utils::str_to_int("Wipe"):
        execute_skill<Wipe,SkillParametersWipe>(name);
        break;
    default:
        throw TaskException("Skill with type " + type + " not known to GenericTask");
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

void GenericTask::get_default_context(nlohmann::json &context){
    context["parameters"] = nlohmann::json();
    context["parameters"]["skill_names"]=nlohmann::json();
    context["parameters"]["skill_types"]=nlohmann::json();
}

}
