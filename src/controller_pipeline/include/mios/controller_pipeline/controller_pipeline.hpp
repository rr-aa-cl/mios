#pragma once

#include "mios/data_structures/percept.hpp"
#include "mios/data_structures/actuator.hpp"
#include "mios/memory/memory.hpp"

#include "franka/control_types.h"

namespace mios {

class ControllerPipeline{
public:
    virtual ~ControllerPipeline(){}
    virtual void initialize(const Percept& p_0,Memory* memory) = 0;
    virtual franka::Finishable* step(const Percept& p, const Actuator& cmd) = 0;
    virtual bool is_valid_command(const franka::Finishable* const cmd) const = 0;
    virtual void terminate() = 0;
    virtual void update_percept(Percept::Controller& p) = 0;
    virtual void context_switch(const Percept& p) = 0;
};

}
