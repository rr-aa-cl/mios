#pragma once

#include "data_structures/percept.hpp"
#include "data_structures/actuator.hpp"
#include "strategy/primitive_strategy.hpp"
#include "utils/exceptions.hpp"
#include <map>

namespace mios {

class Memory;

/**
 * @brief The StrategyData struct provides a convenient way to save strategy related data.
 */
struct StrategyData{
    std::shared_ptr<PrimitiveStrategy> strategy;
    Actuator cmd;
    double weight;
};

/**
 * @brief The ManipulationPrimitive embedds multiple strategies and is itself embedded into a skill. This class takes care of coordinating its strategies and forms the
 * connection between the low-level continuous command space and the high-level hybrid structure of the skill.
 */
class ManipulationPrimitive{
public:
    /**
     * @brief The constructor initializes the class members with the current percept.
     * @param[in] name The name of the primitive
     * @param[in] p_0 The percept at time of construction.
     * @param[in] memory A pointer to the global memory.
     */
    ManipulationPrimitive(const std::string& name, const Percept& p_0, Memory* memory);

    bool get_flag_error() const;
    void set_flag_error();
    std::string get_name() const;

    Actuator* initialize(const Percept &p_0);
    Actuator* initialize(const Percept &p_0, const Actuator &cmd);
    Actuator* step(const Percept& p);
    void terminate(const Percept& p);
    Actuator* cmd_from_buffer();
    Actuator* stop(const Percept &p,double stop_factor=1.0);
    bool is_settled(bool ignore=false) const;
    template<typename T> void create_strategy(const std::string& name,double weight){
        if(m_strategies.find(name)!=m_strategies.end()){
            throw SkillException("Strategy with name " + name + " already exists.");
        }else{
            m_strategies.insert(std::make_pair(name,StrategyData{std::make_shared<T>(),Actuator(m_cmd),weight}));
        }
    }
    template<typename T>std::shared_ptr<T> get_strategy(const std::string& name){
        if(m_strategies.find(name)==m_strategies.end()){
            throw SkillException("Strategy with name " + name + " does not exist.");
        }
        return std::static_pointer_cast<T>(m_strategies.at(name).strategy);
    }
    const std::shared_ptr<PrimitiveStrategy> get_strategy_interface(const std::string& name) const;

private:
    bool compose_command(const Percept &p);

private:
    const std::string m_name;
    Memory* m_memory;
    std::map<std::string, StrategyData> m_strategies;

    Actuator m_cmd;

    bool m_flag_error;
    bool m_flag_initialized;
    bool m_flag_terminated;


};

}
