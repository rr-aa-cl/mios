#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct ConfigSkill_extraction : public ConfigSkill{
    Eigen::Matrix<double,2,1> speed;
    Eigen::Matrix<double,1,1> F_contact;
    Eigen::Matrix<double,1,1> wiggle_a_t;
    Eigen::Matrix<double,1,1> wiggle_a_r;
    Eigen::Matrix<double,1,1> wiggle_a_z;
    Eigen::Matrix<double,1,1> wiggle_f_t;
    Eigen::Matrix<double,1,1> wiggle_f_r;
    Eigen::Matrix<double,1,1> wiggle_f_z;
};

class extraction : public Skill{
public:
    extraction();

    Eigen::Matrix<double,3,3> get_O_R_TF(const Percept& p);

    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);

//    SoundCmd cycle_sound(const Percept &p);
//    LEDCmd cycle_led(const Percept &p);
private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
    bool check_local_err_conditions(const Percept &p);

    Eigen::Matrix<double,4,4> TF_T_hole_est;
    Eigen::Matrix<double,3,1> dir_hole;

};

}
