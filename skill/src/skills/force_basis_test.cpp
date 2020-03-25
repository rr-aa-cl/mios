#include "skills/force_basis_test.hpp"

#include "primitives/mp_force_basis.hpp"

namespace mios{
force_basis_test::force_basis_test():Skill("force_basis_test"){}
force_basis_test::~force_basis_test(){}
bool force_basis_test::read_skill_parameters(const Json::Value& p){
    cpp_utils::read_json_param<double,6,1>(p["F_h_p"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->F_h_p);
    cpp_utils::read_json_param<double,6,1>(p["F_h_d"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->F_h_d);
    cpp_utils::read_json_param<double,6,1>(p["F_h_e"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->F_h_e);

    cpp_utils::read_json_param<double,6,1>(p["ff_fourier_a_a"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->ff_fourier_a_a);
    cpp_utils::read_json_param<double,6,1>(p["ff_fourier_b_a"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->ff_fourier_b_a);
    cpp_utils::read_json_param<double,6,1>(p["ff_fourier_a_f"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->ff_fourier_a_f);
    cpp_utils::read_json_param<double,6,1>(p["ff_fourier_b_f"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->ff_fourier_b_f);
    cpp_utils::read_json_param<double,6,1>(p["ff_fourier_a_phi"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->ff_fourier_a_phi);
    cpp_utils::read_json_param<double,6,1>(p["ff_fourier_b_phi"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->ff_fourier_b_phi);

    if(!cpp_utils::read_json_param<double,4,4>(p["TF_T_EE_g"],static_cast<ConfigSkill_force_basis_test*>(this->_config)->TF_T_EE_g)){
        cpp_utils::print_error("Parameter TF_T_EE_g could not be loaded but is mandatory.");
        return false;
    }

    return true;
}
void force_basis_test::build_primitives(const Percept& p){
    this->insert_mp("basis_1",new mp_force_basis(),p);
    this->set_init_mp("basis_1");

    ConfigMP_mp_force_basis* c_basis = static_cast<ConfigMP_mp_force_basis*>(this->get_mp("basis_1")->get_config());

    ConfigSkill_force_basis_test* c_skill=static_cast<ConfigSkill_force_basis_test*>(this->_config);

    AttractorForceBasis* attr_basis=static_cast<AttractorForceBasis*>(this->get_mp("basis_1")->get_attractor());

    c_basis->F_h_p=c_skill->F_h_p;
    c_basis->F_h_d=c_skill->F_h_d;
    c_basis->F_h_e=c_skill->F_h_e;

    c_basis->ff_fourier_a_a=c_skill->ff_fourier_a_a;
    c_basis->ff_fourier_b_a=c_skill->ff_fourier_b_a;
    c_basis->ff_fourier_a_f=c_skill->ff_fourier_a_f;
    c_basis->ff_fourier_b_f=c_skill->ff_fourier_b_f;
    c_basis->ff_fourier_a_phi=c_skill->ff_fourier_a_phi;
    c_basis->ff_fourier_b_phi=c_skill->ff_fourier_b_phi;

    attr_basis->attr_pose=c_skill->TF_T_EE_g;
    if(this->get_object("goal_pose").id=="none"){
        attr_basis->attr_pose=c_skill->TF_T_EE_g;
    }else{
        attr_basis->attr_pose=this->get_object_pose("goal_pose");
    }

    attr_basis->neighbourhood_X<<0.01,1;

}
std::tuple<bool,std::string> force_basis_test::check_edges(const Percept& p){return std::tuple<bool,std::string>(false,"");}
bool force_basis_test::check_local_suc_conditions(const Percept& p){
    return this->get_mp("basis_1")->in_attractor(p);
}
void force_basis_test::evaluate(){}
void force_basis_test::create_config(){
this->_config=new ConfigSkill_force_basis_test();
}
}
