#include "mios/tasks/generic_task.hpp"
#include "mirmi_cpp_utils/files/files.hpp"

#include "mios/skills/test_skill_1.hpp"
#include "mios/skills/move_to_pose_cart.hpp"
#include "mios/skills/move_to_pose_joint.hpp"
#include "mios/skills/move_to_contact.hpp"
#include "mios/skills/hand_guiding.hpp"
#include "mios/skills/hold_pose.hpp"
#include "mios/skills/generic_wiggle_motion.hpp"
#include "mios/skills/telepresence.hpp"
#include "mios/skills/push.hpp"
#include "mios/skills/shove.hpp"
#include "mios/skills/tip.hpp"
#include "mios/skills/file.hpp"
#include "mios/skills/extraction.hpp"
#include "mios/skills/insertion.hpp"
#include "mios/skills/turn.hpp"
#include "mios/skills/move_trajectory.hpp"
#include "mios/skills/wipe.hpp"

#include "mios/skills/tax_insertion.hpp"
#include "mios/skills/tax_push.hpp"
#include "mios/skills/tax_extraction.hpp"
#include "mios/skills/tax_move.hpp"
#include "mios/skills/tax_grab.hpp"
#include "mios/skills/tax_place.hpp"
#include "mios/skills/tax_press_button.hpp"
#include "mios/skills/tax_turn.hpp"
#include "mios/skills/tax_push.hpp"
#include "mios/skills/tax_tip.hpp"
#include "mios/skills/tax_drag.hpp"
#include "mios/skills/tax_carry.hpp"
#include "mios/skills/tax_shove.hpp"
#include "mios/skills/tax_turn_lever.hpp"
#include "mios/skills/tax_slide_object.hpp"
#include "mios/skills/tax_swipe.hpp"
#include "mios/skills/tax_wipe.hpp"
#include "mios/skills/tax_file.hpp"
#include "mios/skills/tax_bend.hpp"
#include "mios/skills/tax_hammer.hpp"
#include "mios/skills/tax_slide_open.hpp"
#include "mios/skills/draw.hpp"
#include "mios/skills/crank.hpp"
#include "mios/skills/tax_cut.hpp"
#include "mios/skills/tax_displace.hpp"
#include "mios/skills/tax_screw.hpp"
#include "mios/skills/tax_screw_nullspace.hpp"
#include "mios/skills/tax_wrench.hpp"
#include "mios/skills/tax_screw_out.hpp"
#include "mios/skills/ll_interface.hpp"

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
    switch(mirmi_utils::str_to_int(type.c_str())){
    case mirmi_utils::str_to_int("TestSkill1"):
        add_skill<TestSkill1,SkillParametersTestSkill1>(name);
        break;
    case mirmi_utils::str_to_int("HoldPose"):
        add_skill<HoldPose,SkillParametersHoldPose>(name);
        break;
    case mirmi_utils::str_to_int("GenericWiggleMotion"):
        add_skill<GenericWiggleMotion,SkillParametersGenericWiggleMotion>(name);
    case mirmi_utils::str_to_int("TaxMove"):
        add_skill<TaxMove,SkillParametersTaxMove>(name);
        break;
    case mirmi_utils::str_to_int("TaxGrab"):
        add_skill<TaxGrab,SkillParametersTaxGrab>(name);
        break;
    case mirmi_utils::str_to_int("TaxPlace"):
        add_skill<TaxPlace,SkillParametersTaxPlace>(name);
        break;
    case mirmi_utils::str_to_int("TaxInsertion"):
        add_skill<TaxInsertion,SkillParametersTaxInsertion>(name);
        break;
    case mirmi_utils::str_to_int("TaxExtraction"):
        add_skill<TaxExtraction,SkillParametersTaxExtraction>(name);
        break;
    case mirmi_utils::str_to_int("TaxTurn"):
        add_skill<TaxTurn,SkillParametersTaxTurn>(name);
        break;
    case mirmi_utils::str_to_int("TaxPush"):
        add_skill<TaxPush,SkillParametersTaxPush>(name);
        break;
    case mirmi_utils::str_to_int("TaxDrag"):
        add_skill<TaxDrag,SkillParametersTaxDrag>(name);
        break;
    case mirmi_utils::str_to_int("TaxPressButton"):
        add_skill<TaxPressButton,SkillParametersTaxPressButton>(name);
        break;
    case mirmi_utils::str_to_int("TaxTip"):
        add_skill<TaxTip,SkillParametersTaxTip>(name);
        break;
    case mirmi_utils::str_to_int("TaxCarry"):
        add_skill<TaxCarry,SkillParametersTaxCarry>(name);
        break;
    case mirmi_utils::str_to_int("TaxShove"):
        add_skill<TaxShove,SkillParametersTaxShove>(name);
        break;
    case mirmi_utils::str_to_int("TaxTurnLever"):
        add_skill<TaxTurnLever,SkillParametersTaxTurnLever>(name);
        break;
    case mirmi_utils::str_to_int("TaxSlideObject"):
        add_skill<TaxSlideObject,SkillParametersTaxSlideObject>(name);
        break;
    case mirmi_utils::str_to_int("TaxSwipe"):
        add_skill<TaxSwipe,SkillParametersTaxSwipe>(name);
        break;
    case mirmi_utils::str_to_int("TaxBend"):
        add_skill<TaxBend,SkillParametersTaxBend>(name);
        break;
//    case mirmi_utils::str_to_int("TaxHold"):
//        add_skill<TaxHold,SkillParametersTaxHold>(name);
//        break;
    case mirmi_utils::str_to_int("TaxHammer"):
        add_skill<TaxHammer,SkillParametersTaxHammer>(name);
        break;
    default:
        spdlog::error("Skill with type " + type + " not known to GenericTask");
        throw TaskException();
    }
}

void GenericTask::execute_any_skill(unsigned index){
    std::string name = m_skills[index].first;
    std::string type = m_skills[index].second;
    switch(mirmi_utils::str_to_int(type.c_str())){
    case mirmi_utils::str_to_int("TestSkill1"):
        execute_skill<TestSkill1,SkillParametersTestSkill1>(name);
        break;
    case mirmi_utils::str_to_int("MoveToPoseJoint"):
        execute_skill<MoveToPoseJoint,SkillParametersMoveToPoseJoint>(name);
        break;
    case mirmi_utils::str_to_int("MoveToPoseCart"):
        execute_skill<MoveToPoseCart,SkillParametersMoveToPoseCart>(name);
        break;
    case mirmi_utils::str_to_int("MoveToContact"):
        execute_skill<MoveToContact,SkillParametersMoveToContact>(name);
        break;
    case mirmi_utils::str_to_int("GenericWiggleMotion"):
        execute_skill<GenericWiggleMotion,SkillParametersGenericWiggleMotion>(name);
        break;
    case mirmi_utils::str_to_int("HoldPose"):
        execute_skill<HoldPose,SkillParametersHoldPose>(name);
        break;
    case mirmi_utils::str_to_int("HandGuiding"):
        execute_skill<HandGuiding,SkillParametersHandGuiding>(name);
        break;
    case mirmi_utils::str_to_int("Telepresence"):
        execute_skill<Telepresence,SkillParametersTelepresence>(name);
        break;
    case mirmi_utils::str_to_int("Push"):
        execute_skill<Push,SkillParametersPush>(name);
        break;
    case mirmi_utils::str_to_int("Tip"):
        execute_skill<Tip,SkillParametersTip>(name);
        break;
    case mirmi_utils::str_to_int("Shove"):
        execute_skill<Shove,SkillParametersShove>(name);
        break;
    case mirmi_utils::str_to_int("File"):
        execute_skill<File,SkillParametersFile>(name);
        break;
    case mirmi_utils::str_to_int("Extraction"):
        execute_skill<Extraction,SkillParametersExtraction>(name);
        break;
    case mirmi_utils::str_to_int("Insertion"):
        execute_skill<Insertion,SkillParametersInsertion>(name);
        break;

    case mirmi_utils::str_to_int("Wipe"):
        execute_skill<Wipe,SkillParametersWipe>(name);
        break;
    case mirmi_utils::str_to_int("MoveTrajectory"):
        execute_skill<MoveTrajectory,SkillParametersMoveTrajectory>(name);
        break;
    case mirmi_utils::str_to_int("Turn"):
        execute_skill<Turn,SkillParametersTurn>(name);
        break;
    case mirmi_utils::str_to_int("TaxInsertion"):
        execute_skill<TaxInsertion,SkillParametersTaxInsertion>(name);
        break;
    case mirmi_utils::str_to_int("TaxExtraction"):
        execute_skill<TaxExtraction,SkillParametersTaxExtraction>(name);
        break;
    case mirmi_utils::str_to_int("TaxMove"):
        execute_skill<TaxMove,SkillParametersTaxMove>(name);
        break;
    case mirmi_utils::str_to_int("TaxGrab"):
        execute_skill<TaxGrab,SkillParametersTaxGrab>(name);
        break;
    case mirmi_utils::str_to_int("TaxPlace"):
        execute_skill<TaxPlace,SkillParametersTaxPlace>(name);
        break;
    case mirmi_utils::str_to_int("TaxPressButton"):
        execute_skill<TaxPressButton,SkillParametersTaxPressButton>(name);
        break;
    case mirmi_utils::str_to_int("TaxTurn"):
        execute_skill<TaxTurn,SkillParametersTaxTurn>(name);
        break;
    case mirmi_utils::str_to_int("TaxPush"):
        execute_skill<TaxPush,SkillParametersTaxPush>(name);
        break;
    case mirmi_utils::str_to_int("TaxDrag"):
        execute_skill<TaxDrag,SkillParametersTaxDrag>(name);
        break;
    case mirmi_utils::str_to_int("TaxTip"):
        execute_skill<TaxTip,SkillParametersTaxTip>(name);
        break;
    case mirmi_utils::str_to_int("TaxShove"):
        execute_skill<TaxShove,SkillParametersTaxShove>(name);
        break;
    case mirmi_utils::str_to_int("TaxCarry"):
        execute_skill<TaxCarry,SkillParametersTaxCarry>(name);
        break;
    case mirmi_utils::str_to_int("TaxTurnLever"):
        execute_skill<TaxTurnLever,SkillParametersTaxTurnLever>(name);
        break;
    case mirmi_utils::str_to_int("TaxSlideObject"):
        execute_skill<TaxSlideObject,SkillParametersTaxSlideObject>(name);
        break;
    case mirmi_utils::str_to_int("TaxSwipe"):
        execute_skill<TaxSwipe,SkillParametersTaxSwipe>(name);
        break;
    case mirmi_utils::str_to_int("TaxWipe"):
        execute_skill<TaxWipe,SkillParametersTaxWipe>(name);
        break;
    case mirmi_utils::str_to_int("TaxFile"):
        execute_skill<TaxFile,SkillParametersTaxFile>(name);
        break;
    case mirmi_utils::str_to_int("TaxBend"):
        execute_skill<TaxBend,SkillParametersTaxBend>(name);
        break;
//    case mirmi_utils::str_to_int("TaxHold"):
//        execute_skill<TaxHold,SkillParametersTaxHold>(name);
//        break;
    case mirmi_utils::str_to_int("TaxHammer"):
        execute_skill<TaxHammer,SkillParametersTaxHammer>(name);
        break;
    case mirmi_utils::str_to_int("TaxSlideOpen"):
        execute_skill<TaxSlideOpen,SkillParametersTaxSlideOpen>(name);
        break;
    case mirmi_utils::str_to_int("Draw"):
        execute_skill<Draw,SkillParametersDraw>(name);
        break;
    case mirmi_utils::str_to_int("Crank"):
        execute_skill<Crank,SkillParametersCrank>(name);
        break;
    case mirmi_utils::str_to_int("TaxCut"):
        execute_skill<TaxCut,SkillParametersTaxCut>(name);
        break;
    case mirmi_utils::str_to_int("TaxDisplace"):
        execute_skill<TaxDisplace,SkillParametersTaxDisplace>(name);
        break;
    case mirmi_utils::str_to_int("TaxScrew"):
        execute_skill<TaxScrew,SkillParametersTaxScrew>(name);
        break;
    case mirmi_utils::str_to_int("TaxScrewNullspace"):
        execute_skill<TaxScrewNullspace,SkillParametersTaxScrewNullspace>(name);
        break;
    case mirmi_utils::str_to_int("TaxWrench"):
        execute_skill<TaxWrench,SkillParametersTaxWrench>(name);
        break;
    case mirmi_utils::str_to_int("TaxScrewOut"):
        execute_skill<TaxScrewOut,SkillParametersTaxScrewOut>(name);
        break;
    case mirmi_utils::str_to_int("LLInterface"):
        execute_skill<LLInterface,SkillParametersLLInterface>(name);
        break;
    default:
        spdlog::error("Skill with type " + type + " not known to GenericTask");
        throw TaskException();
    }
}

bool GenericTask::read_parameters(const nlohmann::json &params){
    std::vector<std::string> names;
    std::vector<std::string> types;
    m_skills.resize(0);

    if(!mirmi_utils::read_json_param(params,"skill_names",names)){
        spdlog::error("Missing parameter: skill_names.");
        return false;
    }
    if(!mirmi_utils::read_json_param(params,"skill_types",types)){
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
    if(!mirmi_utils::read_json_param(params,"as_queue",m_as_queue)){
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
