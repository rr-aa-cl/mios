#include "tasks/generic_task.hpp"
#include <msrm_cpp_utils/files.hpp>

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
#include "skills/turn.hpp"
#include "skills/move_trajectory.hpp"
#include "skills/wipe.hpp"

#include "skills/tax_insertion.hpp"
#include "skills/tax_extraction.hpp"
#include "skills/tax_move.hpp"
#include "skills/tax_grab.hpp"
#include "skills/tax_place.hpp"
#include "skills/tax_press_button.hpp"
#include "skills/tax_turn.hpp"

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
    if(m_as_queue){
        for(unsigned i=0;i<m_skills.size();i++){
            add_any_skill(i);
        }
        execute_skill_queue();
    }else{
        for(unsigned i=0;i<m_skills.size();i++){
            execute_any_skill(i);
        }
    }
}

void GenericTask::add_any_skill(unsigned int index){
    std::string name = m_skills[index].first;
    std::string type = m_skills[index].second;
    switch(msrm_utils::str_to_int(type.c_str())){
    case msrm_utils::str_to_int("TestSkill1"):
        add_skill<TestSkill1,SkillParametersTestSkill1>(name);
        break;
    case msrm_utils::str_to_int("HoldPose"):
        add_skill<HoldPose,SkillParametersHoldPose>(name);
        break;
    case msrm_utils::str_to_int("TaxMove"):
        add_skill<TaxMove,SkillParametersTaxMove>(name);
        break;
    case msrm_utils::str_to_int("TaxGrab"):
        add_skill<TaxGrab,SkillParametersTaxGrab>(name);
        break;
    case msrm_utils::str_to_int("TaxPlace"):
        add_skill<TaxPlace,SkillParametersTaxPlace>(name);
        break;
    case msrm_utils::str_to_int("TaxInsertion"):
        add_skill<TaxInsertion,SkillParametersTaxInsertion>(name);
        break;
    case msrm_utils::str_to_int("TaxExtraction"):
        add_skill<TaxExtraction,SkillParametersTaxExtraction>(name);
        break;
    case msrm_utils::str_to_int("TaxTurn"):
        add_skill<TaxTurn,SkillParametersTaxTurn>(name);
        break;
    case msrm_utils::str_to_int("TaxPressButton"):
        add_skill<TaxPressButton,SkillParametersTaxPressButton>(name);
        break;
    case msrm_utils::str_to_int("GenericWiggleMotion"):
        add_skill<GenericWiggleMotion,SkillParametersGenericWiggleMotion>(name);
        break;
    default:
        throw TaskException("Skill with type " + type + " not known to GenericTask");
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
    case msrm_utils::str_to_int("MoveTrajectory"):
        execute_skill<MoveTrajectory,SkillParametersMoveTrajectory>(name);
        break;
    case msrm_utils::str_to_int("Turn"):
        execute_skill<Turn,SkillParametersTurn>(name);
        break;
    case msrm_utils::str_to_int("TaxInsertion"):
        execute_skill<TaxInsertion,SkillParametersTaxInsertion>(name);
        break;
    case msrm_utils::str_to_int("TaxExtraction"):
        execute_skill<TaxExtraction,SkillParametersTaxExtraction>(name);
        break;
    case msrm_utils::str_to_int("TaxMove"):
        execute_skill<TaxMove,SkillParametersTaxMove>(name);
        break;
    case msrm_utils::str_to_int("TaxGrab"):
        execute_skill<TaxGrab,SkillParametersTaxGrab>(name);
        break;
    case msrm_utils::str_to_int("TaxPlace"):
        execute_skill<TaxPlace,SkillParametersTaxPlace>(name);
        break;
    case msrm_utils::str_to_int("TaxPressButton"):
        execute_skill<TaxPressButton,SkillParametersTaxPressButton>(name);
        break;
    case msrm_utils::str_to_int("TaxTurn"):
        execute_skill<TaxTurn,SkillParametersTaxTurn>(name);
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
    if(!msrm_utils::read_json_param(params,"as_queue",m_as_queue)){
        m_as_queue=false;
    }
    return true;
}

void GenericTask::get_default_context(nlohmann::json &context){
    context["parameters"] = nlohmann::json();
    context["parameters"]["skill_names"]=nlohmann::json();
    context["parameters"]["skill_types"]=nlohmann::json();
    context["parameters"]["as_queue"]=false;
}

}
