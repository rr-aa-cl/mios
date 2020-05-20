#pragma once

#include "data_structures/percept.hpp"
#include "data_structures/actuator.hpp"

namespace mios {

class Memory;

struct ConfigMP{

};

class Attractor{
    virtual void reached(const Percept& p) = 0;
};

class ManipulationPrimitive{
public:
    ManipulationPrimitive(const std::string& type, const Percept& p_0, std::shared_ptr<ConfigMP> config, std::shared_ptr<Attractor> attractor, Memory* memory, const std::string& id);
    virtual ~ManipulationPrimitive();

    bool get_flag_error() const;
    void set_flag_error();
    std::string get_type() const;
    std::string get_id() const;

    Actuator* initialize(const Percept &p_0);
    Actuator* initialize(const Percept &p_0, const Actuator &cmd);
    void terminate();
    Actuator* cmd_from_buffer();
    Actuator* stop(const Percept &p);
    bool is_settled() const;

    template<typename T>std::shared_ptr<T> get_config() const{
        return std::static_pointer_cast<T>(m_config);
    }
    template<typename T>std::shared_ptr<T> get_attractor() const{
        return std::static_pointer_cast<T>(m_config);
    }
public:
    virtual void i_initialize(const Percept& p_0) = 0;
    virtual Actuator* step(const Percept& p) = 0;
    virtual void i_terminate() = 0;
protected:
    Actuator m_cmd;
    Memory* m_memory;
private:
    std::shared_ptr<ConfigMP> m_config;
    std::shared_ptr<Attractor> m_attractor;
    const std::string m_type;
    const std::string m_id;
    bool m_flag_error;
    bool m_flag_initialized;
    bool m_flag_terminated;
};

}
