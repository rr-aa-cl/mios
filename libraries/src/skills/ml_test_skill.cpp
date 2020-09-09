#include "skills/ml_test_skill.hpp"
#include "strategies/null_strategy.hpp"

namespace mios{

bool SkillParametersMLTestSkill::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"x",x)){
        spdlog::error("Missing parameter: x");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"A",A)){
        A=10;
    }
    if(!msrm_utils::read_json_param(parameters,"selector",selector)){
        selector=0;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersMLTestSkill::get_parameter_list(){
    return {{"x",{}},{"A",{}},{"selector",{}}};
}

MLTestSkill::MLTestSkill(const std::string& id, Memory *memory,Portal* portal):Skill("MLTestSkill",{},id,memory,portal,{ControlMode::mJointVelocity}){

}

std::shared_ptr<ManipulationPrimitive> MLTestSkill::get_initial_mp(const Percept &p_0){
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("mp",p_0);
    mp->create_strategy<NullStrategy>("s_0",1);
    return mp;
}


bool MLTestSkill::check_local_suc_conditions(const Percept& p){
    return true;
}
double MLTestSkill::measure_cost(const Percept &p){
    std::shared_ptr<SkillParametersMLTestSkill> params = get_parameters<SkillParametersMLTestSkill>();
    double y1=0;
    double y2=0;
    for(unsigned i=0;i<params->x.rows();i++){
        y1+=pow(params->x(i),2)-params->A*cos(2*M_PI*params->x(i));
    }
    y1+=params->A*params->x.rows();
    for(unsigned i=0;i<params->x.rows();i++){
        y2+=pow(params->x(i),2);
    }
    double y=params->w_cost_function[0]*y1+params->w_cost_function[1]*y2;
    spdlog::info("MLTestSkill: Costs are " + std::to_string(y));
    return y;
}

}
