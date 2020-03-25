#include "patterns/pattern_success.hpp"

namespace mios {

pattern_success::pattern_success(unsigned n){
    this->n=n;
}

pattern_success::~pattern_success(){

}

void pattern_success::init_pattern(const Percept &p){
    this->_p_success_intensity=0;
    this->cnt_n=0;
}

LEDCmd pattern_success::cycle_led(const Percept *p){
    LEDCmd led_cmd;
    led_cmd.f=2;
    if(this->cnt_n==1){
        led_cmd.set_all_led(0,0,0);
        this->cnt_n=0;
    }else
    if(this->cnt_n==0){
        led_cmd.set_all_led(0,255,0);
        this->cnt_n=1;
    }
    return led_cmd;
}

}
