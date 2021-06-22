#include "mios/utils/exceptions.hpp"
#include "spdlog/spdlog.h"

namespace mios {

TaskException::TaskException(const std::string& msg):m_msg(msg){
}

const char* TaskException::what() const throw(){
    spdlog::error(m_msg);
    return "what(): Task exeption has been thrown, see above error message for more information.";
}

SkillException::SkillException(const std::string& msg):m_msg(msg){
}

const char* SkillException::what() const throw(){
    spdlog::error(m_msg);
    return "what(): Skill exeption has been thrown, see above error message for more information.";
}

}

