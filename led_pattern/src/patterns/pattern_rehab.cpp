#include "patterns/pattern_rehab.hpp"

namespace mios {

pattern_rehab::pattern_rehab(){

}

pattern_rehab::~pattern_rehab(){

}

void pattern_rehab::init_pattern(const Percept &p){
    this->cnt_color=1;
    this->color=10;
}

void pattern_rehab::set_poses(Eigen::Matrix<double,4,4> &r_start, Eigen::Matrix<double,4,4> &r_end){
    _r_end = r_end.block(0,3,3,1);
    _r_start = r_start.block(0,3,3,1);
    Eigen::Matrix<double,3,1>  diff;
    diff.setZero();
    diff = _r_end - _r_start;


    _l = std::sqrt( diff.transpose() * diff);


}

LEDCmd pattern_rehab::cycle_led(const Percept *p){
    LEDCmd led_cmd(10);
    Eigen::Matrix<double,3,1> r_current;
    r_current= p->TF_T_EE.block(0,3,3,1);

//    std::cout << "r_current:"<< r_current << std::endl;


    Eigen::VectorXd m_Xd_dot,m_f_ext;
    m_Xd_dot = Eigen::VectorXd::Zero(3);
    m_f_ext = Eigen::VectorXd::Zero(3);


    m_Xd_dot =  p->TF_dX_d.segment(0,3);
    m_f_ext = p->TF_F_ext.segment(0,3);
    Eigen::VectorXd m_Xd_dotNorm,m_f_extNorm;


    m_Xd_dotNorm = m_Xd_dot/ (std::sqrt( m_Xd_dot.transpose() * m_Xd_dot ) );
    m_f_extNorm = m_f_ext/ (std::sqrt( m_f_ext.transpose() * m_f_ext ));


//    std::cout << "m_Xd_dotNorm:"<< m_Xd_dotNorm << std::endl;
//    std::cout << "m_f_extNorm:"<< m_f_ext << std::endl;
//    std::cout << "m_f_extNorm:"<< m_f_ext << std::endl;


    double psi = std::acos( m_Xd_dotNorm.dot(m_f_extNorm)) *180.0 / M_PI ;

    //std::cout << "psi:"<< psi << std::endl;


    double red_continuous, green_continuous;
    double blendPsiRed, blendPsiGreen;
    double blendFRed, blendFGreen;

    blendFRed   =   0.5* (255.0*(tanh(   std::sqrt(m_f_ext(2)*m_f_ext(2) + m_f_ext(0)*m_f_ext(0))  - 20.0)  +1.0));
    blendFGreen =   0.5* (255.0*(-tanh(  std::sqrt(m_f_ext(2)*m_f_ext(2) + m_f_ext(0)*m_f_ext(0))  - 20.0)  +1.0));

    red_continuous   =   0.5* (180.0*(tanh(   std::sqrt(m_f_ext(2)*m_f_ext(2) + m_f_ext(0)*m_f_ext(0))  - 15.0)  +1.0));
    green_continuous =   0.5* (180.0*(-tanh(  std::sqrt(m_f_ext(2)*m_f_ext(2) + m_f_ext(0)*m_f_ext(0))  - 15.0)  +1.0));



//TODO
//    if(psi > 0.0 &&
//            std::sqrt( m_f_ext.transpose() * m_f_ext ) > 3.0) {
//        red_continuous   = 0.5* (blendFRed*(tanh(  psi  - 35.0)  +1.0));
//        green_continuous = 0.5* (blendFGreen*(-tanh( psi  - 35.0)  +1.0));

//    }
//    else if (psi <= 0.0 &&
//              std::sqrt( m_f_ext.transpose() * m_f_ext ) > 3.0) {
//        red_continuous   =   0.5* (blendFRed*(tanh(  psi  + 35.0)  +1.0));
//        green_continuous =   0.5* (blendFGreen*(-tanh( psi  + 35.0)  +1.0));

//    }
    double blue = 10.0;

    double l_current;
    l_current= std::sqrt( (this->_r_start - r_current).transpose() * (this->_r_start - r_current) );


    double red_continuous1, red_continuous2, red_continuous3, red_continuous4, red_continuous5;
    double green_continuous1, green_continuous2, green_continuous3, green_continuous4, green_continuous5;

//std::cout << "Laenge:"<< l_current << std::endl;

    if (l_current < (this->_l / 5) ) {
        red_continuous1=red_continuous;
        green_continuous1=green_continuous;

        red_continuous2 = 10.0;
        red_continuous3 = 10.0;
        red_continuous4 = 10.0;
        red_continuous5 = 10.0;
        green_continuous2 = 10.0;
        green_continuous3 = 10.0;
        green_continuous4 = 10.0;
        green_continuous5 = 10.0;

    }
    else if ( l_current > (this->_l / 5) &&
              l_current < (2.0*this->_l / 5))
    {
        red_continuous2=red_continuous;
        green_continuous2=green_continuous;

        red_continuous1 = 10.0;
        red_continuous3 = 10.0;
        red_continuous4 = 10.0;
        red_continuous5 = 10.0;
        green_continuous1 = 10.0;
        green_continuous3 = 10.0;
        green_continuous4 = 10.0;
        green_continuous5 = 10.0;
    }
    else if (l_current > (2.0*this->_l / 5) &&
             l_current < (3.0*this->_l / 5)) {
        red_continuous3=red_continuous;
        green_continuous3=green_continuous;

        red_continuous2 = 10.0;
        red_continuous1 = 10.0;
        red_continuous4 = 10.0;
        red_continuous5 = 10.0;
        green_continuous2 = 10.0;
        green_continuous1 = 10.0;
        green_continuous4 = 10.0;
        green_continuous5 = 10.0;
    }
    else if (l_current > (3.0*this->_l / 5) &&
             l_current < (4.0*this->_l / 5)) {
        red_continuous4=red_continuous;
        green_continuous4=green_continuous;
        red_continuous2 = 10.0;
        red_continuous3 = 10.0;
        red_continuous1 = 10.0;
        red_continuous5 = 10.0;
        green_continuous2 = 10.0;
        green_continuous3 = 10.0;
        green_continuous1 = 10.0;
        green_continuous5 = 10.0;
    }
    else if (l_current > (4.0*this->_l / 5)) {
        red_continuous5=red_continuous;
        green_continuous5=green_continuous;

        red_continuous2 = 10.0;
        red_continuous3 = 10.0;
        red_continuous4 = 10.0;
        red_continuous1 = 10.0;
        green_continuous2 = 10.0;
        green_continuous3 = 10.0;
        green_continuous4 = 10.0;
        green_continuous1 = 10.0;
    }

    led_cmd.set_led("left", red_continuous1, green_continuous1, blue);
    led_cmd.set_led("middle", red_continuous2, green_continuous2, blue);
    led_cmd.set_led("right", red_continuous3, green_continuous3, blue);
    led_cmd.set_led("far-right", red_continuous4, green_continuous4, blue);
    led_cmd.set_led("far-left", red_continuous5, green_continuous5, blue);





    return led_cmd;
}
}
