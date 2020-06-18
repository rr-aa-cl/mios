#pragma once

#include "data_structures/actuator.hpp"
#include "data_structures/percept.hpp"
#include <eigen3/Eigen/Core>

namespace mios {

/**
 * @brief The PrimitiveStrategy class is an interface for concrete strategies which calculate the skill commands according to a user-defined policy.
 * A strategy is embedded into a manipulation primitive.
 */
class PrimitiveStrategy{
public:
    PrimitiveStrategy(bool command_TF_T_EE_d=false,bool command_TF_F_d=false,bool command_q_d=false,bool command_q_d_nullspace=false, bool command_tau_d=false);
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
    bool is_commanding_TF_T_EE_d() const;
    bool is_commanding_TF_F_d() const;
    bool is_commanding_q_d() const;
    bool is_commanding_q_d_nullspace() const;
    bool is_commanding_tau_d() const;

private:
    const bool m_command_TF_T_EE_d;
    const bool m_command_TF_F_d;
    const bool m_command_q_d;
    const bool m_command_q_d_nullspace;
    const bool m_command_tau_d;
};

}
