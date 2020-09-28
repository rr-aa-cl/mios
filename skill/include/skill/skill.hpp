#pragma once

#include <unordered_map>
#include <unordered_set>
#include <atomic>
#include <thread>
#include <msrm_utils/json.hpp>

#include "manipulation_primitive/manipulation_primitive.hpp"
#include "memory/memory.hpp"
#include "portal/portal.hpp"

#include "data_structures/percept.hpp"
#include "data_structures/actuator.hpp"
#include "data_structures/parameters.hpp"

#include "utils/exceptions.hpp"
#include "data_structures/results.hpp"

#include <spdlog/spdlog.h>


namespace mios {

class Object;

enum SkillLifeCycle{slInit,slTransition,slExecution,slSettle,slTerminate};

/**
 * The skill base class provides handling of manipulation primitives, error handling and more. Every skill inherits from this class.
 */
class Skill{
public:
    /**
     * The skill base constructor. It is called by the constructor of any derived skill class.
     * @param[in] type The type id of the skill.
     */
    Skill(const std::string& type, const std::unordered_set<std::string> &objects, const std::string &id, Memory *memory, Portal* portal, std::set<ControlMode> control_modes);

    /**
     * The skill destructor.
     */
    virtual ~Skill();
    /**
     * Initializes the skill by building the manipulation primitives, calculating the task frame, preparing the output struct
     * and making validity checks.
     * @param[in] p Percept struct.
     * @return Returns true if initialization was successful, false otherwise.
     */
    bool initialize(const Percept &p);

    /**
     * Calculates O_R_TF for this skill. It can be static, provided in the task description or based on the percept at time of skill execution.
     * @param[in] p Percept struct.
     * @return Return O_R_TF to be used for this skill. Return the 0 matrix to use the values from the task description.
     */
    virtual Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const;

    /**
     * Main execution loop of the skill. Manages all manipulation primitives, local and global conditions.
     * @param[in] p Percept struct.
     * @return Output of the skill.
     */
    Actuator *cycle(const Percept& p);

    /**
     * Is called at the end of skill execution. Terminates manipulation primitives and calls the evaluate function.
     */
    void terminate(const Percept &p);

    /**
     * Invokes a skill failure, this will stop skill execution and set the success indicator to false.
     */
    void invoke_failure();

    /**
     * Invokes a skill success, this will stop skill execution and set the success indicator to true.
     */
    void invoke_success();

    /**
     * Sets the pause status for the skill. When paused, all twist and wrench commands are set to zero.
     * @param[in] pause True pauses the skill, false means normal execution.
     */
    void set_pause(bool pause);

    void append_error(const std::string &error);

    /**
     * Returns a const reference to the evaluation struct of this skill.
     * @return A const reference to the evaluation struct of this skill.
     */
    const SkillResult& get_result() const;

    /**
     * Returns a pointer to the configuration struct of this skill. It is explicitly allowed to modify the struct.
     * @return A pointer to the configuratin struct of this skill.
     */

    /**
     * Returns the type id of the skill.
     * @return Type id of the skill.
     */
    const std::string& get_type() const;

    /**
     * Returns the instance id of the skill.
     * @return Instance id of the skill.
     */
    const std::string& get_id() const;

    void read_configuration(const nlohmann::json & p);


    /**
     * Manually connects an existing object (in the knowledge base) to a valid skill object.
     * @param[in] o_type Skill object id.
     * @param o Id of object in knowledge base.
     */

    bool ground_objects();

    /**
     * Returns a const reference to the indicated skill object.
     * @param[in] o Id of skill object.
     * @return A const reference to object.
     *
     * @throw SkillException if o is not a skill object.
     */
    const Object *get_object(const std::string& o) const;
    Object* update_object(const std::string& o);


    /**
     * Returns pose of object.
     * @param o Id of skill object.
     * @param TF Determines whether the pose should be given in task frame or base frame.
     * @return Object pose.
     */
    Eigen::Matrix<double,4,4> get_object_pose_O(const std::string& object_name) const;
    Eigen::Matrix<double,4,4> get_object_pose_T(const std::string& object_name) const;
    Eigen::Matrix<double,4,4> get_object_grasp_pose_T(const std::string& object_name) const;
    Eigen::Matrix<double,4,4> get_object_grasp_pose_O(const std::string& object_name) const;

    virtual void write_custom_results(nlohmann::json& custom_results);
    nlohmann::json& get_custom_results();

    const std::set<ControlMode>* get_valid_control_modes() const;
protected:

    const std::shared_ptr<ManipulationPrimitive> get_active_mp() const;
    void write_costs(double cost_suc, double cost_err);

    /**
     * Returns a pointer to the specified manipulation primitive.
     * @param[in] mp Id of manipulation primitive.
     * @return Pointer to manipulation primitive with id mp.
     *
     * @throw SkillException if mp does not exist in this skill.
     */
    std::shared_ptr<ManipulationPrimitive> get_mp(const std::string& mp) const;

    /**
     * This function may be overwritten by the developer and may contain any additional functionality of the skill that does not fit into the other functions.
     * @param[in] p Percept struct.
     */
    virtual void auxiliaries(const Percept& p);

    /**
     * Specify the initial manipulation primitive.
     * @param[in] id Id of the manipulation primitive.
     *
     * @throw SkillException if mp id does not exist.
     */
    void set_init_mp(const std::string& name);

    /**
     * Creates manipulation primitive.
     * @param[in] id Id of the manipulation primitive.
     * @param[in] mp Pointer to manipulation primitive object. Implicit creation is recommended.
     * @param[in] p Percept struct.
     * @param[in] c Pointer to global configuration struct of the skill.
     *
     * @throw SkillException if manipulation primitive with id already exists.
     */
    std::shared_ptr<ManipulationPrimitive> create_mp(const std::string& name, const Percept &p);


    /**
     * Checks global error conditions that hold for any skill. These are violations of maximum external wrench or joint torques, maximum execution time or
     * external trigger.
     * @param[in] p Percept struct.
     * @return True if global error conditions have been violated, false otherwise.
     *
     * @throw SkillException if configuration struct has not been set by developer via the function "create_config".
     */
    bool check_global_err_conditions(const Percept& p) const;

    /**
     * Checks global success conditions that hold for any skill. These are external trigger.
     * @param[in] p Percept struct.
     * @return True if global success conditions have been fulfilled, false otherwise.
     */
    bool check_global_suc_conditions(const Percept& p) const;

    Memory* m_memory;
    Portal* m_portal;

protected:
    virtual void parallels();
    /**
     * Checks the skills preconditions that have to be defined by the developer. This function is optional, the default return value is true.
     * Preconditions are checked at start of skill execution.
     * @param p
     * @return True if preconditions are fulfilled, false otherwise.
     */
    virtual bool check_local_pre_conditions(const Percept& p);

    /**
     * Checks local error conditions that have to be defined by the developer. This function is optional, the default return value is false.
     * If the error conditions have been fulfilled, the skill is stopped unsuccessfully.
     * @param[in] p Percept struct.
     * @return True if user-defined error conditions have been fulfilled, false otherwise.
     */
    virtual bool check_local_err_conditions(const Percept& p);

    /**
     * Checks local success conditions that have to be defined by the developer. This function is mandatory. If the success conditions have been fulfilled
     * the skill has to fullfil the exit condition as well to successfully terminate.
     * @param[in] p Percept struct.
     * @return Must return true if local success conditions have been fulfilled, false otherwise.
     */
    virtual bool check_local_suc_conditions(const Percept& p) = 0;

    /**
     * Checks the exit conditions that have to be defined by the developer. This function is mandatory. If the exit conditions have been fulfilled as well as the success conditions
     * the skill will terminate successfully. This makes it possible to seperate the success conditions from the nominal end of the skill execution.
     * @param[in] p Percept struct.
     * @return Must return true if exit conditions have been fulfilled, false otherwise.
     */
    virtual bool check_local_ex_conditions(const Percept& p);

    virtual std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept& p);
    virtual std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) = 0;
    template<typename T> std::shared_ptr<T> get_parameters(){
        return std::static_pointer_cast<T>(m_memory->get_parameters()->skill);
    }
    template<typename T> const std::shared_ptr<T> read_parameters() const{
        return std::static_pointer_cast<T>(m_memory->read_parameters()->skill);
    }

    virtual void update_internal_models(const Percept &p);
    virtual void update_policies(const Percept& p);
    virtual double get_goal_heuristic(const Percept& p);

private:
    std::shared_ptr<ManipulationPrimitive> m_active_mp;
    SkillResult m_result;

    void run_parallels();
    void stop_parallels();
    void terminate_parallels();
    bool has_settled();
    SkillCost measure_cost(const Percept& p);
    virtual double get_custom_cost(const Percept& p);

    std::unordered_map<std::string,std::shared_ptr<ManipulationPrimitive> > m_mp_graph;
    std::string m_init_mp;

    std::unordered_map<std::string,Object*> m_grounded_objects;
    const std::set<ControlMode> m_control_modes;
    std::chrono::high_resolution_clock::time_point m_time_start;

    std::unordered_map<std::string,double> m_costs;

private:
    SkillLifeCycle m_life_cycle;
    std::atomic<bool> m_flag_invoke_failure;
    std::atomic<bool> m_flag_invoke_success;
    std::atomic<bool> m_flag_pause;
    std::atomic<bool> m_flag_parallels_running;
    std::atomic<bool> m_flag_run_parallels;
    double m_stop_factor;
    std::thread m_thr_parallels;

private:
    const std::string m_type;
    const std::string m_id;
    const std::unordered_set<std::string> m_objects;

private:
    bool m_msg_local_success;
    bool m_msg_global_success;

private:
    double m_cost_contact_forces_sum;
    double m_cost_effort_avg_sum;

};

}
