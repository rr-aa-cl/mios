#pragma once

#include <list>
#include <map>
#include <unordered_set>
#include <unordered_map>
#include <atomic>
#include <stdlib.h>
#include <memory>
#include <msrm_utils/json.hpp>
#include <spdlog/spdlog.h>

#include "task/taskobserver.hpp"
#include "skill/skill_engine.hpp"
#include "utils/exceptions.hpp"
#include "data_structures/results.hpp"
#include "skill/skill.hpp"

namespace mios {

class Memory;
class Core;


/**
 * The task class is embedded into task handling procedures that ensure robust execution. Any derived class inherits the necessary properties.
 */
class Task{
public:
    Task(const std::string &id, Core* core);
    virtual ~Task();

    /**
     * Stops the currently running task.
     * @param[in] nominal Indicates whether the the stop is nominal. Non-nominal stops take effect immediately,
     * nominal stops fierst scale down any output to zero according to valid limits.
     * @param[in] success Indicates whether the task is considered successful after the stop.
     * @param recover[in] Determines whether the recovery routine of the task (and all its subtasks) should be executed.
     * @param cost_suc[in] Sets the cost for the task execution in case of success.
     * @param cost_err[in] Sets the cost for the task execution in case of failure.
     */
    void stop_task(bool raise_exception=false, bool recover=true, bool empty_queue=false);

    /**
     * Loads its description and that of all subtasks and all skill descriptions from the knowledge base. Furthermore it merges all user provided parameters.
     * @param overwrite[in] User parameters that overwrite any data loaded from the knowledge base.
     * @param core Pointer to the core module.
     * @return Returns true if the task and all its subtasks and skills were successfully loaded.
     */
    bool load_context(const nlohmann::json &user_context);
    const nlohmann::json &get_context() const;
    void overwrite_context(const std::string& skill_name, const std::string& parameter_type, const std::string& parameter, const nlohmann::json &value);
    void overwrite_context(const std::string& subtask_name, const std::string& skill_name, const std::string& parameter_type, const std::string& parameter, const nlohmann::json &value);

    /**
     * Implements task execution in derived tasks.
     */
    virtual void execute() = 0;

    /**
     * Implements recovery routine in derived tasks, optional.
     */
    virtual void recover_task();

    /**
     * Implements the initialization routine in derived tasks. This function is called in the beginning of a task execution.
     */
    virtual void initialize_context() = 0;

    /**
     * Implements the evaluation routine. The user has to define how the members of the evaluation struct are set. This function is called at the end of a nominal task execution.
     * @return Return the current evaluation struct (will change to void in future updates).
     */
    virtual void evaluate() = 0;

    /**
     * Starts the recovery routine of the task. This function is called at the end of a task execution if it has terminated before the nominal end.
     */
    void start_recovery();
    /**
     * Completes the recovery routine of the task. This function is called after task recovery to signal the task handler that the recovery routine is complete.
     */
    void complete_recovery();

    /**
     * This function is called to determine whether recovery is necessay/desired.
     * @return Returns true if recovery is necessary/desired.
     */
    bool do_recovery() const;

    /**
     * Returns the type if of the task.
     * @return The type id of the task.
     */
    std::string get_id() const;

    /**
     * Returns the stop flag. If the stop flag is true the task has been stopped.
     * @return The stop flag.
     */
    bool get_stop_flag() const;

    /**
     * Returns the recovery flag. If the recovery flag is true the task is currently in recovery mode.
     * @return The recovery flag.
     */
    bool get_recovery_flag() const;

    /**
     * Reads user-defined task parameters. This function is called during the loading process, however, it can be called manually during
     * initialization or execution of a parent task.
     * @param[in] params User-defined parameters in json format.
     * @return Returns true if all is in order (according to developer of derived task).
     */
    virtual bool read_parameters(const nlohmann::json& params);

    std::string get_uuid() const;
    TaskResult get_result() const;
    TaskResult get_subtask_result(const std::string& subtask_name) const;
    void notify_observers();
    void subscribe(std::shared_ptr<TaskObserver> observer);

protected:

    // helper functions

    /**
     * Sets the internal state to the specified value.
     * @param[in] state User-defined state value.
     */
    void set_state(const std::string &state);

    /**
     * Returns the current value of the internal state.
     * @return Current value of internal state.
     */
    std::string get_state() const;

    /**
     * Sleeps for at least 1 ms. This function has to be used for sleeps during task execution. Otherwise stop commands would have no effect.
     */
    void sleep_1ms() const;

    /**
     * Checks whether the robot is currently grasping something. Note, this function returns the indicator of the gripper state. It does
     * not consider whether it acutally grasps an object or whether the gripper is just closed.
     * @return True if gripper is grasping, false otherwise.
     */
    bool is_grasping() const;

    /**
     * This function attempts to grasp the specified object. The obejct has to exist in the knowledge base. In the current implementation the gripper
     * closes regardless of whether there is an object between the fingers and its width.
     * @param[in] o Id of the object in the knowledge base.
     * @param[in] width Desired width after releasing. Must be within valid limits of gripper. Default value is -1 which refers to maximum width.
     * @param[in] speed Desired speed of gripper. Default is 1 m/s.
     * @param[in] force Desired grasping force. Default is 30 N.
     * @return True if grasping was successful, false otherwise.
     */
    bool grasp_object(const std::string& name, double speed=1);

    /**
     * Releases any object that is currently grasped. The fingers are opened to maximum width.
     * @param[in] width Desired width after releasing. Must be within valid limits of gripper. Default value is -1 which refers to maximum width.
     * @param[in] speed Desired speed of gripper. Default is 1 m/s.
     * @return True if releasing was successful, false otherwise.
     */
    bool release_object(double speed=1);

    /**
     * Moves the gripper fingers to the specified position.
     * @param[in] width Desired width.
     * @param[in] speed Desired speed of the finger movement.
     * @return True if moving was successful, false otherwise.
     */
    bool move_gripper(double width,double speed);

    /**
     * Requests the current percept struct from the core module.
     * @param[in] O_R_TF If specified the percept is calculated in the given task frame.
     * @return Current percept struct.
     */
    bool get_percept(Percept& percept,std::optional<Eigen::Matrix<double, 3, 3> > O_R_T);


    bool reserve_skill(const std::string& name);
    bool insert_skill(const std::string& name, const std::string& type);
    bool reserve_subtask(const std::string& name);

    /**
     * Executes the skill with the given name id. Use this ONLY in the execute_task function.
     * @param s Name id of skill.
     * @param log If true, all skill data will be logged and saved at the end of the task execution. (WIP)
     *
     * @throw TaskException if core or knowledge base are not connected, if skill with name id s does not exist in this task, or if the skill
     * has been terminated by a non-nominal event.
     */

    void write_skill_object(const std::string skill,const std::string groundable,const std::string object);

//    void execute_skill(const std::string& name);
    template<typename T_skill, typename T_param>void execute_skill(const std::string &name){
        std::scoped_lock<std::mutex> lock(m_mtx_execution);
        if(m_context["skills"].find(name)==m_context["skills"].end()){
            spdlog::error("Skill with id "+name+" not in this task. Check the task context for consistency. Stopping task.");
            stop_task(true);
            throw TaskException("Skill with id "+name+" not in this task. Check the task context for consistency. Stopping task.");
        }
        if(m_flag_stop){
            return;
        }
        Percept p;
        if(!get_percept(p,{})){
            throw TaskException("Could not refresh perception.");
        }

        std::shared_ptr<Skill> skill = std::make_shared<T_skill>(name,m_memory,p);
        m_memory->get_parameters()->create_skill_parameters<T_param>();
        spdlog::info("Executing skill "+name+".");
        bool result=m_skill_engine->execute_skill(m_context,skill);
        m_result.skill_results.insert(std::make_pair(name,skill->get_result()));
        if(skill->get_result().exception){
            m_flag_stop = true;
        }
        if(!result){
            throw TaskException("Could not execute skill " + name + ".");
        }
    }

    /**
     * Executes the subtask with the given name id. Use this ONLY in the execute_task function.
     * @param t Name id of subtask.
     *
     * @throw TaskException if core or knowledge base are not connected or if subtask with name id s does not exist in this task.
     */
    void execute_subtask(const std::string& task_id, const std::string task_name);

    /**
     * Executes the specified desk timeline.
     * @param id Name of the desk timeline.
     */
    void execute_desk_timeline(const std::string& id);

    void write_result(bool success, double cost_suc, double cost_err, std::optional<nlohmann::json> custom_results);

protected:

private:

    /**
     * Checks the task description for syntax errors. Returns false if necessary elements are missing or if additional invalids ones are present.
     * @param[in] descr The task description to check.
     * @return True if the given task description is valid, false otherwise.
     */
    bool check_context(const nlohmann::json& default_context, const nlohmann::json &user_context) const;
    static std::string generate_uuid();

    TaskResult m_result;
    std::unordered_map<std::string,TaskResult> m_subtask_results;

    std::unordered_set<std::string> m_reserved_skills;
    std::unordered_set<std::string> m_reserved_subtasks;

    nlohmann::json m_context;
    Core* m_core;
    Memory* m_memory;
    SkillEngine* m_skill_engine;
    std::atomic<bool> m_flag_stop;
    std::atomic<bool> m_flag_recover;
    std::atomic<bool> m_flag_in_recovery;

    std::string m_state;

    const std::string m_id;
    const std::string m_uuid;

    std::set<std::shared_ptr<TaskObserver> > m_observers;

    std::shared_ptr<Task> m_active_subtask;

    std::mutex m_mtx_execution;

};

}
