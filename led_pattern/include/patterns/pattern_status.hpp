#pragma once

#include "led_pattern/led_pattern.hpp"

namespace mios {

class pattern_status : public LEDPattern{
public:
    pattern_status();
    ~pattern_status();

    void init_pattern(const Percept &p);
    LEDCmd cycle_led(const Percept* p);

private:

};

}

