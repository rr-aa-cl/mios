#pragma once

#include <iostream>
#include <stdexcept>

namespace mios {

class TaskException :  public std::exception{
public:
    virtual const char* what() const throw();
};

class SkillException :  public std::exception{
public:
    virtual const char* what() const throw();
};

}
