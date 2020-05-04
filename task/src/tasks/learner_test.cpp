#include "tasks/learner_test.hpp"
namespace mios{
learner_test::learner_test():Task("learner_test"){
}
learner_test::~learner_test(){
}
void learner_test::initialize_task(){
    this->create_skill<learner_test_skill>("learner_test");
}
void learner_test::execute_task(){
    this->execute_skill("learner_test");
}
const EvalTask& learner_test::evaluate_task(){
    // Rastrigin function

    this->_eval_task.cost_suc=this->get_skill("learner_test")->get_eval().cost_suc;
    this->_eval_task.cost_err=this->get_skill("learner_test")->get_eval().cost_err;
    this->_eval_task.success=this->get_skill("learner_test")->get_eval().success;

    return this->_eval_task;
}
bool learner_test::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param<double,6,1>(params,"x",this->x)){
        msrm_utils::print_error("Missing parameter: x [6x1]");
        return false;
    }
    return true;
}
}
