#include "tasks/manipulation_test.hpp"

#include "skills/force_basis_test.hpp"

namespace mios{
manipulation_test::manipulation_test():Task("manipulation_test"){
}
manipulation_test::~manipulation_test(){
}
void manipulation_test::initialize_task(){
    this->create_skill(new force_basis_test(),"manipulation_basis");
}
void manipulation_test::execute_task(){
    this->execute_skill("manipulation_basis");
}
const EvalTask& manipulation_test::evaluate_task(){
return this->_eval_task;
}
}
