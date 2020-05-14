#pragma once

#include "utils/percept.hpp"
#include "utils/actuator.hpp"
#include "knowledge_base/knowledge_base.hpp"

#include <franka/control_types.h>

namespace mios {

class ControllerPipeline{
public:
    virtual void initialize(const Percept& p_0,KnowledgeBase* kb) = 0;
    virtual franka::Finishable* step(const Percept& p, const Actuator& cmd) = 0;
    virtual void terminate() = 0;
    virtual void update_percept(Percept::Controller& p) = 0;
};

}
