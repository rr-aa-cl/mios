#pragma once

#include <map>
#include <string>
#include "skill/skill.hpp"

namespace mios{

class Memory;
class Portal;

class SkillLibrary{
public:
    SkillLibrary(Memory* memory, Portal* portal);
    const std::map<std::string, std::shared_ptr<Skill> > *get_skills() const;
private:

    std::map<std::string,std::shared_ptr<Skill> > m_skills;
};

}
