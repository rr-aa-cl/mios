#pragma once

#include <map>
#include <string>
#include "skill/skill.hpp"
#include "data_structures/parameters.hpp"

namespace mios{

class Memory;
class Portal;

class SkillLibrary{
public:
    SkillLibrary(Memory* memory, Portal* portal);
    const std::map<std::string, std::shared_ptr<Skill> > *get_skills() const;
    const std::map<std::string, std::shared_ptr<SkillParameters> > *get_skill_parameters() const;
private:

    std::map<std::string,std::shared_ptr<Skill> > m_skills;
    std::map<std::string,std::shared_ptr<SkillParameters> > m_skill_parameters;
};

}
