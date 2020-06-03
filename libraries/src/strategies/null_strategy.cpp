#include "strategy/null_strategy.hpp"

namespace mios {

void NullStrategy::initialize(const Percept &p_0){

}

void NullStrategy::get_next_command(Actuator &cmd, const Percept &p){

}

void NullStrategy::terminate(const Percept &p){

}

bool NullStrategy::finished(){
    return false;
}

}
