#include "tasks/null_task.hpp"

namespace mios {

NullTask::NullTask(Core* core):Task("NullTask",core){

}

void NullTask::initialize_context(){

}

void NullTask::execute(){

}

}
