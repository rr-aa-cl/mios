#pragma once

#include "utils/types.hpp"
#include "knowledge_base/local_memory.hpp"

namespace mios {

class LEDPattern{
public:
    LEDPattern();
    ~LEDPattern();

    virtual void init_pattern(const Percept& p) = 0;
    virtual LEDCmd cycle_led(const Percept* p) = 0;

private:

};

}
