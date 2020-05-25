#pragma once

#include "data_structures/percept.hpp"
#include "data_structures/actuator.hpp"

namespace mios {

class Memory;

class Attractor{
public:
    virtual bool reached(const Percept& p) = 0;
};

class MPParameters{

};

class ManipulationPrimitive{
public:
    ManipulationPrimitive(const std::string& type, const std::string& name, const Percept& p_0, std::shared_ptr<MPParameters> parameters, std::shared_ptr<Attractor> attractor, Memory* memory);
    virtual ~ManipulationPrimitive();

    bool get_flag_error() const;
    void set_flag_error();
    std::string get_type() const;
    std::string get_name() const;

    Actuator* initialize(const Percept &p_0);
    Actuator* initialize(const Percept &p_0, const Actuator &cmd);
    void terminate();
    Actuator* cmd_from_buffer();
    Actuator* stop(const Percept &p);
    bool is_settled() const;

    template<typename T>std::shared_ptr<T> get_parameters(){
        return std::static_pointer_cast<T>(m_parameters);
    }
    template<typename T>std::shared_ptr<T> get_attractor(){
        return std::static_pointer_cast<T>(m_attractor);
    }
public:
    virtual void i_initialize(const Percept& p_0) = 0;
    virtual Actuator* step(const Percept& p) = 0;
    virtual void i_terminate() = 0;
protected:
    Memory* m_memory;
    Actuator m_cmd;
private:
    bool m_flag_error;
    bool m_flag_initialized;
    bool m_flag_terminated;

    std::shared_ptr<MPParameters> m_parameters;
    std::shared_ptr<Attractor> m_attractor;

    const std::string m_type;
    const std::string m_name;
};

}
