#include "patterns/pattern_disappointment.hpp"

namespace mios {

pattern_disappointment::pattern_disappointment(unsigned n){
    this->n=n;
}

pattern_disappointment::~pattern_disappointment(){

}

void pattern_disappointment::init_pattern(const Percept &p){
    this->_p_disappointment_intensity=0;
    this->cnt_n=0;
}

LEDCmd pattern_disappointment::cycle_led(const Percept *p){
    LEDCmd led_cmd;
    led_cmd.f=2;
    if(this->cnt_n==1){
        led_cmd.set_all_led(0,0,0);
        this->cnt_n=0;
    }else
    if(this->cnt_n==0){
        led_cmd.set_all_led(255,0,0);
        this->cnt_n=1;
    }
    return led_cmd;
}

}
