#pragma once

#include "led_pattern/led_pattern.hpp"

namespace mios {

class pattern_interactive : public LEDPattern{
public:
    pattern_interactive();
    ~pattern_interactive();

    void init_pattern(const Percept &p);
    LEDCmd cycle_led(const Percept* p);

private:

    std::map<std::string,std::array<unsigned,3> > base_color;
    unsigned max_intensity;
    unsigned min_intensity;
    unsigned cnt_intensity;
    int cnt_direction;

};

}

