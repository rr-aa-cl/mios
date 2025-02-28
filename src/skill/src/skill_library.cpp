#include "mios/skill/skill_library.hpp"

#include "mios/skill/skill.hpp"
#include "mios/data_structures/parameters.hpp"

#include "mios/skills/tax_insertion.hpp"
#include "mios/skills/tax_extraction.hpp"
#include "mios/skills/tax_move.hpp"
#include "mios/skills/tax_grab.hpp"
#include "mios/skills/tax_place.hpp"
#include "mios/skills/tax_press_button.hpp"
#include "mios/skills/tax_turn.hpp"
#include "mios/skills/tax_push.hpp"
#include "mios/skills/tax_drag.hpp"
#include "mios/skills/tax_tip.hpp"
#include "mios/skills/tax_shove.hpp"
#include "mios/skills/tax_carry.hpp"
#include "mios/skills/tax_turn_lever.hpp"
#include "mios/skills/tax_slide_object.hpp"
#include "mios/skills/tax_swipe.hpp"
#include "mios/skills/tax_wipe.hpp"
#include "mios/skills/tax_file.hpp"
#include "mios/skills/tax_bend.hpp"
//#include "mios/skills/tax_hold.hpp"
#include "mios/skills/tax_hammer.hpp"

#include "mios/skills/test_skill_1.hpp"
#include "mios/skills/generic_wiggle_motion.hpp"
#include "mios/skills/move_to_pose_joint.hpp"
#include "mios/skills/hold_pose.hpp"
#include "mios/skills/move_to_pose_cart.hpp"
#include "mios/skills/move_to_contact.hpp"
#include "mios/skills/hand_guiding.hpp"
#include "mios/skills/telepresence.hpp"
#include "mios/skills/push.hpp"
#include "mios/skills/shove.hpp"
#include "mios/skills/tip.hpp"
#include "mios/skills/file.hpp"
#include "mios/skills/extraction.hpp"
#include "mios/skills/insertion.hpp"
#include "mios/skills/wipe.hpp"
#include "mios/skills/turn.hpp"
#include "mios/skills/move_trajectory.hpp"
#include "mios/skills/ml_test_skill.hpp"
#include "mios/skills/tax_insertion.hpp"
#include "mios/skills/tax_extraction.hpp"
#include "mios/skills/tax_move.hpp"
#include "mios/skills/tax_grab.hpp"
#include "mios/skills/tax_place.hpp"
#include "mios/skills/tax_press_button.hpp"
#include "mios/skills/tax_turn.hpp"
#include "mios/skills/tax_slide_open.hpp"
#include "mios/skills/tax_push.hpp"
#include "mios/skills/draw.hpp"
#include "mios/skills/crank.hpp"
#include "mios/skills/tax_cut.hpp"
#include "mios/skills/tax_displace.hpp"
#include "mios/skills/tax_screw.hpp"
#include "mios/skills/tax_screw_nullspace.hpp"
#include "mios/skills/tax_wrench.hpp"
#include "mios/skills/tax_screw_out.hpp"
#include "mios/skills/ll_interface.hpp"

#include "spdlog/spdlog.h"

namespace mios {

SkillLibrary::SkillLibrary(){
    spdlog::trace("SkillLibrary::SkillLibrary");
    m_skill_parameters.insert(std::make_pair("TestSkill1",std::make_shared<SkillParametersTestSkill1>()));
    m_skill_parameters.insert(std::make_pair("GenericWiggleMotion",std::make_shared<SkillParametersGenericWiggleMotion>()));
    m_skill_parameters.insert(std::make_pair("MoveToPoseJoint",std::make_shared<SkillParametersMoveToPoseJoint>()));
    m_skill_parameters.insert(std::make_pair("HoldPose",std::make_shared<SkillParametersHoldPose>()));
    m_skill_parameters.insert(std::make_pair("MoveToPoseCart",std::make_shared<SkillParametersMoveToPoseCart>()));
    m_skill_parameters.insert(std::make_pair("MoveToContact",std::make_shared<SkillParametersMoveToContact>()));
    m_skill_parameters.insert(std::make_pair("HandGuiding",std::make_shared<SkillParametersHandGuiding>()));
    m_skill_parameters.insert(std::make_pair("Telepresence",std::make_shared<SkillParametersTelepresence>()));
    m_skill_parameters.insert(std::make_pair("Push",std::make_shared<SkillParametersPush>()));
    m_skill_parameters.insert(std::make_pair("Shove",std::make_shared<SkillParametersShove>()));
    m_skill_parameters.insert(std::make_pair("Tip",std::make_shared<SkillParametersTip>()));
    m_skill_parameters.insert(std::make_pair("File",std::make_shared<SkillParametersFile>()));
    m_skill_parameters.insert(std::make_pair("Extraction",std::make_shared<SkillParametersExtraction>()));
    m_skill_parameters.insert(std::make_pair("Insertion",std::make_shared<SkillParametersInsertion>()));
    m_skill_parameters.insert(std::make_pair("Wipe",std::make_shared<SkillParametersWipe>()));
    m_skill_parameters.insert(std::make_pair("Turn",std::make_shared<SkillParametersTurn>()));
    m_skill_parameters.insert(std::make_pair("MoveTrajectory",std::make_shared<SkillParametersMoveTrajectory>()));
    m_skill_parameters.insert(std::make_pair("MLTestSkill",std::make_shared<SkillParametersMLTestSkill>()));
    m_skill_parameters.insert(std::make_pair("TaxInsertion",std::make_shared<SkillParametersTaxInsertion>()));
    m_skill_parameters.insert(std::make_pair("TaxExtraction",std::make_shared<SkillParametersTaxExtraction>()));
    m_skill_parameters.insert(std::make_pair("TaxMove",std::make_shared<SkillParametersTaxMove>()));
    m_skill_parameters.insert(std::make_pair("TaxGrab",std::make_shared<SkillParametersTaxGrab>()));
    m_skill_parameters.insert(std::make_pair("TaxPlace",std::make_shared<SkillParametersTaxPlace>()));
    m_skill_parameters.insert(std::make_pair("TaxPressButton",std::make_shared<SkillParametersTaxPressButton>()));
    m_skill_parameters.insert(std::make_pair("TaxTurn",std::make_shared<SkillParametersTaxTurn>()));
    m_skill_parameters.insert(std::make_pair("TaxPush",std::make_shared<SkillParametersTaxPush>()));
    m_skill_parameters.insert(std::make_pair("TaxDrag",std::make_shared<SkillParametersTaxDrag>()));
    m_skill_parameters.insert(std::make_pair("TaxTip",std::make_shared<SkillParametersTaxTip>()));
    m_skill_parameters.insert(std::make_pair("TaxShove",std::make_shared<SkillParametersTaxShove>()));
    m_skill_parameters.insert(std::make_pair("TaxCarry",std::make_shared<SkillParametersTaxCarry>()));
    m_skill_parameters.insert(std::make_pair("TaxTurnLever",std::make_shared<SkillParametersTaxTurnLever>()));
    m_skill_parameters.insert(std::make_pair("TaxSlideObject",std::make_shared<SkillParametersTaxSlideObject>()));
    m_skill_parameters.insert(std::make_pair("TaxSwipe",std::make_shared<SkillParametersTaxSwipe>()));
    m_skill_parameters.insert(std::make_pair("TaxWipe",std::make_shared<SkillParametersTaxWipe>()));
    m_skill_parameters.insert(std::make_pair("TaxFile",std::make_shared<SkillParametersTaxFile>()));
    m_skill_parameters.insert(std::make_pair("TaxBend",std::make_shared<SkillParametersTaxBend>()));
//    m_skill_parameters.insert(std::make_pair("TaxHold",std::make_shared<SkillParametersTaxHold>()));
    m_skill_parameters.insert(std::make_pair("TaxHammer",std::make_shared<SkillParametersTaxHammer>()));
    m_skill_parameters.insert(std::make_pair("TaxSlideOpen",std::make_shared<SkillParametersTaxSlideOpen>()));
    m_skill_parameters.insert(std::make_pair("Draw",std::make_shared<SkillParametersDraw>()));
    m_skill_parameters.insert(std::make_pair("Crank",std::make_shared<SkillParametersCrank>()));
    m_skill_parameters.insert(std::make_pair("TaxCut",std::make_shared<SkillParametersTaxCut>()));
    m_skill_parameters.insert(std::make_pair("TaxDisplace",std::make_shared<SkillParametersTaxDisplace>()));
    m_skill_parameters.insert(std::make_pair("TaxScrew",std::make_shared<SkillParametersTaxScrew>()));
    m_skill_parameters.insert(std::make_pair("TaxScrewNullspace",std::make_shared<SkillParametersTaxScrew>()));
    m_skill_parameters.insert(std::make_pair("TaxWrench",std::make_shared<SkillParametersTaxWrench>()));
    m_skill_parameters.insert(std::make_pair("TaxScrewOut",std::make_shared<SkillParametersTaxScrewOut>()));
    m_skill_parameters.insert(std::make_pair("TaxPush",std::make_shared<SkillParametersTaxPush>()));
    m_skill_parameters.insert(std::make_pair("LLInterface",std::make_shared<SkillParametersLLInterface>()));
}

const std::unordered_map<std::string,std::shared_ptr<Skill> >* SkillLibrary::get_skills() const{
    spdlog::trace("SkillLibrary::get_skills");
    return &m_skills;
}

const std::unordered_map<std::string,std::shared_ptr<SkillParameters> >* SkillLibrary::get_skill_parameters() const{
    spdlog::trace("SkillLibrary::get_skill_parameters");
    return &m_skill_parameters;
}

}
