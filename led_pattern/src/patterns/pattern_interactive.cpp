#include "patterns/pattern_interactive.hpp"

namespace mios {

pattern_interactive::pattern_interactive(){
}

pattern_interactive::~pattern_interactive(){

}

void pattern_interactive::init_pattern(const Percept &p){
    std::map<std::string, std::array<unsigned, 3> > colors;
    this->base_color=colors;

    this->cnt_direction=1;
    this->max_intensity=150;
    this->min_intensity=50;
}

LEDCmd pattern_interactive::cycle_led(const Percept *p){
    LEDCmd led_cmd(10);

    if(this->cnt_intensity>this->max_intensity){
        this->cnt_direction=-2;
    }
    if(this->cnt_intensity<this->min_intensity){
        this->cnt_direction=2;
    }
    this->cnt_intensity+=this->cnt_direction;

    led_cmd.set_led("far-left",0,0,this->cnt_intensity);
    led_cmd.set_led("left",0,0,this->cnt_intensity);
    led_cmd.set_led("middle",0,0,this->cnt_intensity);
    led_cmd.set_led("right",0,0,this->cnt_intensity);
    led_cmd.set_led("far-right",0,0,this->cnt_intensity);
    return led_cmd;
}

}
