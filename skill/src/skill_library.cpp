#include "skill/skill_library.hpp"
#include "memory/memory.hpp"
#include "portal/portal.hpp"
#include "data_structures/percept.hpp"

#include "skills/test_skill_1.hpp"
#include "skills/generic_wiggle_motion.hpp"
#include "skills/move_to_pose_joint.hpp"
#include "skills/hold_pose.hpp"
#include "skills/move_to_pose_cart.hpp"
#include "skills/move_to_contact.hpp"
#include "skills/hand_guiding.hpp"
#include "skills/telepresence.hpp"
#include "skills/push.hpp"
#include "skills/shove.hpp"
#include "skills/tip.hpp"
#include "skills/file.hpp"
#include "skills/extraction.hpp"
#include "skills/insertion.hpp"
#include "skills/wipe.hpp"
#include "skills/turn.hpp"
#include "skills/move_trajectory.hpp"
#include "skills/ml_test_skill.hpp"

#include "skills/tax_insertion.hpp"
#include "skills/tax_extraction.hpp"
#include "skills/tax_move.hpp"
#include "skills/tax_grab.hpp"
#include "skills/tax_place.hpp"
#include "skills/tax_press_button.hpp"
#include "skills/tax_turn.hpp"
#include "skills/tax_push.hpp"
#include "skills/tax_pull.hpp"
#include "skills/tax_tip.hpp"

namespace mios {

SkillLibrary::SkillLibrary(Memory* memory, Portal* portal){
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
    m_skill_parameters.insert(std::make_pair("TaxPull",std::make_shared<SkillParametersTaxPull>()));
    m_skill_parameters.insert(std::make_pair("TaxTip",std::make_shared<SkillParametersTaxTip>()));
}

const std::map<std::string,std::shared_ptr<Skill> >* SkillLibrary::get_skills() const{
    return &m_skills;
}

const std::map<std::string,std::shared_ptr<SkillParameters> >* SkillLibrary::get_skill_parameters() const{
    return &m_skill_parameters;
}

}
