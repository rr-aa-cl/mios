#pragma once

#include "manipulation_primitive/manipulation_primitive.hpp"


namespace mios {

struct MPParametersNullPrimitive : public MPParameters{

};

class NullAttractor : public Attractor{
    bool reached(const Percept& p);
};

class NullPrimitive : public ManipulationPrimitive{
public:
    NullPrimitive(const std::string& name, const Percept& p_0, std::shared_ptr<MPParameters> parameters, std::shared_ptr<Attractor> attractor, Memory* memory);

    void i_initialize(const Percept &p_0) override;
    Actuator * step(const Percept &p) override;
    void i_terminate() override;
};

}
