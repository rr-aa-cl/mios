#pragma once

#include "led_pattern/led_pattern.hpp"

namespace mios {

class pattern_white : public LEDPattern{
public:
    pattern_white();
    ~pattern_white();

    void init_pattern(const Percept &p);
    LEDCmd cycle_led(const Percept* p);

private:

    int cnt_color;
    int color;

};

}

