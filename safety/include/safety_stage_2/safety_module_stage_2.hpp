#pragma once

#include "data_structures/actuator.hpp"
#include "data_structures/percept.hpp"
#include "memory/memory.hpp"
#include <eigen3/Eigen/Core>

namespace mios {

class SafetyModuleStage2{
public:
    virtual ~SafetyModuleStage2(){}
    virtual void initialize(const Percept& p_0,const Memory* memory) = 0;
    virtual void step(const Percept& p,franka::Finishable* cmd) = 0;
    virtual void terminate() = 0;

};

}
