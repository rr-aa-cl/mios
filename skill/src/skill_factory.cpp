#include "skill/skill_factory.hpp"

#include "skills/motions_generic_wiggle.hpp"
#include "skills/hold_pose.hpp"

#include <msrm_utils/files.hpp>

namespace mios{

SkillType SkillFactory::get_skill_type(const std::string &skill){
    switch(msrm_utils::str_to_int(skill.c_str())){
    case msrm_utils::str_to_int("WiggleMotion"):
        return SkillType::stWiggleMotion;
    case msrm_utils::str_to_int("HandGuiding"):
        return SkillType::stHandGuiding;
    case msrm_utils::str_to_int("TestSkill1"):
        return SkillType::stTestSkill1;
    case msrm_utils::str_to_int("HoldPose"):
        return SkillType::stHoldPose;
    case msrm_utils::str_to_int("MoveToPoseJoint"):
        return SkillType::stMoveToPoseJoint;
    default: return SkillType::stNullSkill;
    }
}

std::shared_ptr<Task> TaskFactory::create_task(TaskName task,Core* core){
    switch(task){
    case TaskName::TaskName_IdleTask:
        return std::make_shared<IdleTask>(core);
    case TaskName::TaskName_TestTask1:
        return std::make_shared<TestTask1>(core);
    case TaskName::TaskName_TestTask2:
        return std::make_shared<TestTask2>(core);
    case TaskName::TaskName_TestTask3:
        return std::make_shared<TestTask3>(core);
    default:
        return std::make_shared<IdleTask>(core);

    }
}



}
