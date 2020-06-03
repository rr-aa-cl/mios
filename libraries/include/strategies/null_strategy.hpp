#pragma once

#include "strategy/primitive_strategy.hpp"

namespace mios {

class NullStrategy : public PrimitiveStrategy{
public:
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;
};

}
