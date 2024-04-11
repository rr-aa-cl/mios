#include "mios/strategy/primitive_strategy.hpp"

namespace mios{

PrimitiveStrategy::PrimitiveStrategy(const std::set<CommandPattern>& command_pattern):
m_command_pattern(command_pattern){

}

std::set<CommandPattern> PrimitiveStrategy::get_command_pattern() const{
    return m_command_pattern;
}

}

void DynamicSystemInterpolation(double& y, double& dy, double goal){
    double a = 0.9;
    double b = 0.3;
    double ddy = a*(b*(goal-y)-dy);
    dy = dy + ddy;
    y = y + dy;
}