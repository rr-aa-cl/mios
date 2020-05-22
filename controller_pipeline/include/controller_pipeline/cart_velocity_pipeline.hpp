#pragma once

#include "controller_pipeline/controller_pipeline.hpp"

namespace mios {

class CartVelocityControllerPipeline : public ControllerPipeline{
public:
    CartVelocityControllerPipeline();
    void initialize(const Percept& p_0,Memory* memory) override;
    franka::Finishable* step(const Percept &p, const Actuator &cmd) override;
    bool is_valid_command(const franka::Finishable* const cmd) const;
    void update_percept(Percept::Controller &p) override;
    void terminate() override;
private:
    franka::CartesianVelocities m_panda_cmd;
};

}
