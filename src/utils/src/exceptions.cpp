#include "mios/utils/exceptions.hpp"
#include "spdlog/spdlog.h"

namespace mios {

const char* TaskException::what() const throw(){
    return "what(): Task exeption has been thrown.";
}

const char* SkillException::what() const throw(){
    return "what(): Skill exeption has been thrown.";
}

}

