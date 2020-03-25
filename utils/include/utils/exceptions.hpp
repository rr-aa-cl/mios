#pragma once

#include <iostream>
#include <stdexcept>

#include "cpp_utils/output.hpp"

namespace mios {


class ParameterLoadException :  public std::exception{
public:
    virtual const char* what() const throw(){
        return "what(): Could not load a parameter from database.";
    }
};

class TaskException :  public std::exception{
public:
    TaskException(const std::string& msg){
        this->msg=msg;
    }
    virtual const char* what() const throw(){
        cpp_utils::print_error(msg);
        return "what(): Task exeption has been thrown, see above error message for more information.";
    }
private:
    std::string msg;
};

class SkillException :  public std::exception{
public:
    SkillException(const std::string& msg){
        this->msg=msg;
    }
    virtual const char* what() const throw(){
        cpp_utils::print_error(msg);
        return "what(): Skill exeption has been thrown, see above error message for more information.";
    }
private:
    std::string msg;
};

class CoreException :  public std::exception{
public:
    CoreException(const std::string& msg){
        this->msg=msg;
    }
    virtual const char* what() const throw(){
        cpp_utils::print_error(msg);
        return "what(): Core exeption has been thrown, see above error message for more information.";
    }
private:
    std::string msg;
};

}
