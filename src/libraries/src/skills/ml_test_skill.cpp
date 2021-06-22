#include "mios/skills/ml_test_skill.hpp"
#include "mios/strategies/null_strategy.hpp"

namespace mios{

bool SkillParametersMLTestSkill::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"x",x)){
        spdlog::error("Missing parameter: x");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"A",A)){
        A=10;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"x_0",x_0)){
        x_0.setZero();
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersMLTestSkill::get_parameter_list(){
    return {{"x",{}},{"A",{}},{"x_0",{}}};
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

SkillCost MLTestSkill::measure_cost(const Percept &p){
    std::shared_ptr<SkillParametersMLTestSkill> params = get_parameters<SkillParametersMLTestSkill>();
    double y1=0;
    double y2=0;
    double y3=0;
    // Rastrigin benchmark function
    for(unsigned i=0;i<params->x.rows();i++){
        y1+=pow(params->x(i),2)-params->A*cos(2*M_PI*params->x(i));
    }
    y1+=params->A*params->x.rows();
    // Sphere benchmark function
    for(unsigned i=0;i<params->x.rows();i++){
        y2+=pow(params->x(i),2);
    }

    for(unsigned i=0;i<params->x.rows();i++){
        y3+=pow(params->x(i)-params->x_0(i),2);
    }
    SkillCost cost;
    cost.time=y1;
    cost.contact_forces=y2;
    cost.effort_avg=y3;
    return cost;
}

}
