#include "patterns/pattern_custom.hpp"

namespace mios {

pattern_custom::pattern_custom(std::map<std::string, std::array<unsigned, 3> > colors){
this->colors=colors;
}

pattern_custom::~pattern_custom(){

}

void pattern_custom::init_pattern(const Percept &p){
}

LEDCmd pattern_custom::cycle_led(const Percept *p){
    LEDCmd led_cmd(1);

    led_cmd.set_led("far-left",this->colors["far-left"][0],this->colors["far-left"][1],this->colors["far-left"][2]);
    led_cmd.set_led("left",this->colors["left"][0],this->colors["left"][1],this->colors["left"][2]);
    led_cmd.set_led("middle",this->colors["middle"][0],this->colors["middle"][1],this->colors["middle"][2]);
    led_cmd.set_led("right",this->colors["right"][0],this->colors["right"][1],this->colors["right"][2]);
    led_cmd.set_led("far-right",this->colors["far-right"][0],this->colors["far-right"][1],this->colors["far-right"][2]);
    return led_cmd;
}

}
