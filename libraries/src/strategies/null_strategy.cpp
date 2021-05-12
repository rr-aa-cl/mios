#include "strategies/null_strategy.hpp"
#include "utils/exceptions.hpp"

namespace mios {

void NullStrategy::initialize(const Percept &p_0){

}

void NullStrategy::get_next_command(Actuator &cmd, const Percept &p){

}

void NullStrategy::terminate(const Percept &p){

}

bool NullStrategy::finished(){
    throw SkillException("Call to a NullStrategy.");
    return true;
}

}
