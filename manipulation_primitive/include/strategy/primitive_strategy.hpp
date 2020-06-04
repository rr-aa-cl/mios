#pragma once

#include "data_structures/actuator.hpp"
#include "data_structures/percept.hpp"
#include <eigen3/Eigen/Core>

namespace mios {

class PrimitiveStrategy{
public:
    virtual void initialize(const Percept& p_0) = 0;
    virtual void get_next_command(Actuator& cmd, const Percept& p) = 0;
    virtual void terminate(const Percept& p) = 0;
    virtual bool finished() = 0;
};

}
