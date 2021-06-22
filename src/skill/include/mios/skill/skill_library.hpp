#pragma once

#include <unordered_map>
#include <string>
#include <memory>

namespace mios{

class Skill;
class SkillParameters;

class SkillLibrary{
public:
    SkillLibrary();
    const std::unordered_map<std::string, std::shared_ptr<Skill> > *get_skills() const;
    const std::unordered_map<std::string, std::shared_ptr<SkillParameters> > *get_skill_parameters() const;
private:

    std::unordered_map<std::string,std::shared_ptr<Skill> > m_skills;
    std::unordered_map<std::string,std::shared_ptr<SkillParameters> > m_skill_parameters;
};

}
