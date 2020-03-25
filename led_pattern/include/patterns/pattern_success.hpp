#pragma once

#include "led_pattern/led_pattern.hpp"

namespace mios {

class pattern_success : public LEDPattern{
public:
    pattern_success(unsigned n=0);
    ~pattern_success();

    void init_pattern(const Percept &p);
    LEDCmd cycle_led(const Percept* p);

private:

    int _p_success_intensity;
    unsigned n;
    unsigned cnt_n;
};

}

