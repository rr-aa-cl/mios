#include "patterns/pattern_status.hpp"

namespace mios {

pattern_status::pattern_status(){
}

pattern_status::~pattern_status(){

}

void pattern_status::init_pattern(const Percept &p){
}

LEDCmd pattern_status::cycle_led(const Percept *p){
    LEDCmd led_cmd(2);

    if(p->robot_mode==franka::RobotMode::kIdle){
        led_cmd.set_led("far-left",0,0,100);
        led_cmd.set_led("left",0,0,100);
        led_cmd.set_led("middle",0,0,100);
        led_cmd.set_led("right",0,0,100);
        led_cmd.set_led("far-right",0,0,100);
    }
    if(p->robot_mode==franka::RobotMode::kUserStopped){
        led_cmd.set_led("far-left",0,150,0);
        led_cmd.set_led("left",0,150,0);
        led_cmd.set_led("middle",0,150,0);
        led_cmd.set_led("right",0,150,0);
        led_cmd.set_led("far-right",0,150,0);
    }
    return led_cmd;
}

}
