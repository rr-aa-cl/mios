#pragma once

#include <map>
#include <memory>


namespace mios{
class Memory;
class Percept;
class Skill;

enum SkillType{stHoldPose,stWiggleMotion,stHandGuiding,stMoveToPoseJoint,stTestSkill1,stNullSkill};

class SkillFactory{
public:
    static SkillType get_skill_type(const std::string& skill);
    static std::shared_ptr<Skill> create_skill(SkillType type, const std::string& name, Memory* memory, Percept* percept);
};
}
