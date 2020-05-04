#include "skills/learner_test_skill.hpp"
namespace mios{
learner_test_skill::learner_test_skill():Skill("learner_test_skill"){}
learner_test_skill::~learner_test_skill(){}
bool learner_test_skill::read_skill_parameters(const nlohmann::json& p){
    std::shared_ptr<ConfigSkill_learner_test_skill> c = this->get_config<ConfigSkill_learner_test_skill>();
    msrm_utils::read_json_param<double,6,1>(p,"x",c->x);
    msrm_utils::read_json_param(p,"A",c->A);
    msrm_utils::read_json_param(p,"selector",c->selector);
    return true;
}
void learner_test_skill::build_primitives(const Percept& p){
    this->insert_mp<mp_basic>("dummy",p);
    this->set_init_mp("dummy");

}
std::tuple<bool,std::string> learner_test_skill::check_edges(const Percept& p){return std::tuple<bool,std::string>(false,"");}
bool learner_test_skill::check_local_suc_conditions(const Percept& p){return true;}
void learner_test_skill::evaluate(){
    std::shared_ptr<ConfigSkill_learner_test_skill> c = this->get_config<ConfigSkill_learner_test_skill>();
    double y1=0;
    double y2=0;
    for(unsigned i=0;i<c->x.rows();i++){
        y1+=pow(c->x(i),2)+c->A*cos(2*M_PI*c->x(i));
    }
    y1+=c->A*c->x.rows();
    for(unsigned i=0;i<c->x.rows();i++){
        y2+=pow(c->x(i),2);
    }
    double y=c->w_cost_function[0]*y1+c->w_cost_function[1]*y2;
    this->_eval.cost_suc=y;
    this->_eval.cost_err=y;
    this->_eval.success=true;
}
void learner_test_skill::create_config(){
    this->_config=std::make_shared<ConfigSkill_learner_test_skill>();
}
}
