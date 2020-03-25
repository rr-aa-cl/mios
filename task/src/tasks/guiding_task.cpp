#include "tasks/guiding_task.hpp"
namespace mios{
guiding_task::guiding_task():Task("guiding_task"){
}
guiding_task::~guiding_task(){
}
void guiding_task::initialize_task(){
}
void guiding_task::execute_task(){
}
const EvalTask& guiding_task::evaluate_task(){
return this->_eval_task;
}
}
