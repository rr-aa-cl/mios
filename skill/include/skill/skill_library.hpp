#pragma once

#include <set>
#include "skill/skill.hpp"

namespace mios{

class SkillLibrary{
public:
    SkillLibrary();
    const std::set<std::shared_ptr<Skill> >* get_skills() const;
private:

    std::set<std::shared_ptr<Skill> > m_skills;
};

}
