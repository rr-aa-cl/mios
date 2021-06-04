#include "strategy/primitive_strategy.hpp"

namespace mios{

PrimitiveStrategy::PrimitiveStrategy(const std::set<CommandPattern>& command_pattern):
m_command_pattern(command_pattern){

}

std::set<CommandPattern> PrimitiveStrategy::get_command_pattern() const{
    return m_command_pattern;
}

}
