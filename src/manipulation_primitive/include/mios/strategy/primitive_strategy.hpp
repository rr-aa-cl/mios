#pragma once

#include "mios/data_structures/actuator.hpp"
#include "mios/data_structures/percept.hpp"
#include "Eigen/Core"

#include <set>

namespace mios {

/**
 * @brief The PrimitiveStrategy class is an interface for concrete strategies which calculate the skill commands according to a user-defined policy.
 * A strategy is embedded into a manipulation primitive.
 */
class PrimitiveStrategy{
public:
    PrimitiveStrategy(const std::set<CommandPattern> &command_pattern={});
    virtual ~PrimitiveStrategy(){}
    /**
     * @brief This method is called once at the beginning of the execution of the embedding manipulation primitive. It can be used to initialize custom members.
     * @param[in] p_0 The percept at initialization.
     */
    virtual void initialize(const Percept& p_0) = 0;
    /**
     * @brief This method calculates the skill commands for the next timestep.
     * @param[out] cmd The actuator object is passed by reference and may be modified by the strategy.
     * @param[in] p The current percept.
     */
    virtual void get_next_command(Actuator& cmd, const Percept& p) = 0;
    /**
     * @brief This method is called once at the end of the execution of the embedding manipulation primitive. It can be used to properly terminate and destruct custom members.
     * @param[in] p The percept at time of termination.
     */
    virtual void terminate(const Percept& p) = 0;
    /**
     * @brief This method may be used to indicate when a strategy is finished (if this applies to the strategy). The function is called every timestep.
     * @return True may indicate that the strategy is finished. How the return value is handled depends on the skill.
     */
    virtual bool finished() = 0;

public:
    std::set<CommandPattern> get_command_pattern() const;

private:
    const std::set<CommandPattern> m_command_pattern;
};

}
