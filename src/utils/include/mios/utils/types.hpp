#pragma once

#include <string>
#include <map>
#include <deque>

namespace mios {


struct ControlReturnType{
    ControlReturnType(bool exception_in,std::string error_in,std::string error_msg_in){
        exception=exception_in;
        error=error_in;
        error_msg=error_msg_in;
    }
    bool exception;
    std::string error;
    std::string error_msg;
};

}
