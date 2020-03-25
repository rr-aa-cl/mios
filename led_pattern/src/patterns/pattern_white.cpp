#include "patterns/pattern_white.hpp"

namespace mios {

pattern_white::pattern_white(){

}

pattern_white::~pattern_white(){

}

void pattern_white::init_pattern(const Percept &p){
    this->cnt_color=1;
    this->color=10;
}

LEDCmd pattern_white::cycle_led(const Percept *p){
    LEDCmd led_cmd(1);
    led_cmd.set_all_led(255,255,255);
    return led_cmd;
}

}
