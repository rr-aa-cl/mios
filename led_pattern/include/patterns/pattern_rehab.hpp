#pragma once

#include "led_pattern/led_pattern.hpp"

namespace mios {

class pattern_rehab : public LEDPattern{
public:
    pattern_rehab();
    ~pattern_rehab();

    void init_pattern(const Percept &p);
    LEDCmd cycle_led(const Percept* p);

    void set_poses(Eigen::Matrix<double,4,4> &r_start, Eigen::Matrix<double,4,4> &r_end);


private:

    //Compute Led ID and color
    Eigen::Matrix<double,3,1> _r_start;
    Eigen::Matrix<double,3,1> _r_end;
    double _l;

    int cnt_color;
    int color;

};

}

