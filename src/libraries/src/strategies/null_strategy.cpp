#include "mios/strategies/null_strategy.hpp"

namespace mios {

void NullStrategy::initialize([[maybe_unused]] const Percept &p_0){

}

void NullStrategy::get_next_command([[maybe_unused]] Actuator &cmd, [[maybe_unused]] const Percept &p){

}

void NullStrategy::terminate([[maybe_unused]] const Percept &p){

}

bool NullStrategy::finished(){
    return true;
}

}
