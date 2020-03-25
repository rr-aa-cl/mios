#pragma once

#include "led_pattern/led_pattern.hpp"

namespace mios {

class pattern_custom : public LEDPattern{
public:
    pattern_custom(std::map<std::string,std::array<unsigned,3> > colors);
    ~pattern_custom();

    void init_pattern(const Percept &p);
    LEDCmd cycle_led(const Percept* p);

private:

    std::map<std::string,std::array<unsigned,3> > colors;

};

}

