#include "skill/skill_library.hpp"

#include "skills/test_skill_1.hpp"
#include "skills/move_to_pose_cart.hpp"
#include "skills/move_to_pose_joint.hpp"
#include "skills/move_to_contact.hpp"
#include "skills/hand_guiding.hpp"
#include "skills/hold_pose.hpp"
#include "skills/motions_generic_wiggle.hpp"
#include "skills/telepresence.hpp"
#include "skills/push.hpp"
#include "skills/shove.hpp"
#include "skills/tip.hpp"
#include "skills/file.hpp"
#include "skills/extraction.hpp"
#include "skills/insertion.hpp"

namespace mios {

SkillLibrary::SkillLibrary(){
    m_skills.insert(std::make_shared<TestSkill1>());
    m_skills.insert(std::make_shared<MoveToPoseCart>());
    m_skills.insert(std::make_shared<MoveToPoseJoint>());
    m_skills.insert(std::make_shared<MoveToContact>());
    m_skills.insert(std::make_shared<HandGuiding>());
    m_skills.insert(std::make_shared<HoldPose>());
    m_skills.insert(std::make_shared<GenericWiggleMotion>());
    m_skills.insert(std::make_shared<Telepresence>());
    m_skills.insert(std::make_shared<Push>());
    m_skills.insert(std::make_shared<Shove>());
    m_skills.insert(std::make_shared<Tip>());
    m_skills.insert(std::make_shared<File>());
    m_skills.insert(std::make_shared<Extraction>());
    m_skills.insert(std::make_shared<Insertion>());
}

const std::set<std::shared_ptr<Skill> >* SkillLibrary::get_skills() const{
    return &m_skills;
}

}
