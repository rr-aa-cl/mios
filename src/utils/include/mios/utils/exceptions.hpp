#pragma once

#include <iostream>
#include <stdexcept>

namespace mios {

class TaskException :  public std::exception{
public:
    TaskException(const std::string& msg);
    virtual const char* what() const throw();
private:
    std::string m_msg;
};

class SkillException :  public std::exception{
public:
    SkillException(const std::string& msg);
    virtual const char* what() const throw();
private:
    std::string m_msg;
};

}
