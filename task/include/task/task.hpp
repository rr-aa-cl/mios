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

#include "skill/skill.hpp"
#include "core/core.hpp"
#include "task/taskobserver.hpp"

namespace mios {

class Memory;


/**
 * The evaluation struct contains quality metrics about the task execution as well as necessary information for the task handling procedures.
 */
struct TaskResult{
    /**
     * The constructor of the struct is by default called to build a nominal, unsuccessful task evaluation.
     * @param nominal
     */
    TaskResult(){
        cost_suc=0;
        cost_err=0;
        success=false;
        exception=false;
        empty_queue=false;
        custom_results=nlohmann::json();
        errors.resize(0);
    }

    std::unordered_map<std::string,SkillResult> m_skill_results;
    std::unordered_map<std::string,TaskResult> m_subtask_results;

    double cost_suc;
    double cost_err;
    bool success;
    bool exception;
    bool empty_queue;
    nlohmann::json custom_results;
    std::vector<std::string> errors;
};


/**
 * The task class is embedded into task handling procedures that ensure robust execution. Any derived class inherits the necessary properties.
 */
class Task{
public:
    Task(const std::string &id, Core* core);
    virtual ~Task();

    /**
     * Resets some of the flags and indicators of this task and its skills, but not the subtasks.
     */
    void reset_soft();

    /**
     * Stops the currently running task.
     * @param[in] nominal Indicates whether the the stop is nominal. Non-nominal stops take effect immediately,
     * nominal stops fierst scale down any output to zero according to valid limits.
     * @param[in] success Indicates whether the task is considered successful after the stop.
     * @param recover[in] Determines whether the recovery routine of the task (and all its subtasks) should be executed.
     * @param cost_suc[in] Sets the cost for the task execution in case of success.
     * @param cost_err[in] Sets the cost for the task execution in case of failure.
     */
    void stop_task(bool raise_exception=false, bool success=false, bool recover=true, bool empty_queue=false, double cost_suc=0, double cost_err=0);

    /**
     * Will be removed in future updates.
     */
    void abort_task();

    /**
     * Loads its description and that of all subtasks and all skill descriptions from the knowledge base. Furthermore it merges all user provided parameters.
     * @param overwrite[in] User parameters that overwrite any data loaded from the knowledge base.
     * @param core Pointer to the core module.
     * @return Returns true if the task and all its subtasks and skills were successfully loaded.
     */
    bool load_context(const nlohmann::json &user_context, nlohmann::json& active_context);

    /**
     * Implements task execution in derived tasks.
     */
    virtual void execute_task() = 0;

    /**
     * Implements recovery routine in derived tasks, optional.
     */
    virtual void recover_task();

    /**
     * Implements the initialization routine in derived tasks. This function is called in the beginning of a task execution.
     */
    virtual void initialize_task() = 0;

    /**
     * Implements the evaluation routine. The user has to define how the members of the evaluation struct are set. This function is called at the end of a nominal task execution.
     * @return Return the current evaluation struct (will change to void in future updates).
     */
    virtual void evaluate_task() = 0;

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
     * Returns the current evaluation struct of the task.
     * @return The current evaluation struct of the task.
     */
    EvalTask get_eval() const;

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
    void notify_observers();
    void subscribe(std::shared_ptr<TaskObserver> observer);

protected:

    /**
     * Returns a pointer to the specified skill.
     * @param[in] id Name id of the skill.
     * @return Pointer to specified skill.
     */
    std::shared_ptr<Skill> get_skill(const std::string& id) const;

    /**
     * Returns a pointer to the specified subtask.
     * @param[in] id Name id of the subtask.
     * @return Pointer to specified subtask.
     */
    std::shared_ptr<Task> get_subtask(const std::string& id) const;

    /**
     * Loads the specified LED pattern. The pattern starts immediately after loading.
     * @param[in] pattern Pointer to LED pattern class. Recommended is an implicit construction of the object.
     */
    void load_led_pattern(std::shared_ptr<LEDPattern> pattern);
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
    bool grasp_object(const std::string& o, double width=-1, double speed=1, double force=30, bool check_width=false);

    /**
     * Releases any object that is currently grasped. The fingers are opened to maximum width.
     * @param[in] width Desired width after releasing. Must be within valid limits of gripper. Default value is -1 which refers to maximum width.
     * @param[in] speed Desired speed of gripper. Default is 1 m/s.
     * @return True if releasing was successful, false otherwise.
     */
    bool release_object(double width=-1,double speed=1);

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
    const Percept& request_percept(Eigen::Matrix<double, 3, 3> O_R_TF=Eigen::Matrix<double,3,3>::Zero(3,3));


    bool reserve_skill(const std::string& name);
    bool reserve_subtask(const std::string& name);

    /**
     * Executes the skill with the given name id. Use this ONLY in the execute_task function.
     * @param s Name id of skill.
     * @param log If true, all skill data will be logged and saved at the end of the task execution. (WIP)
     *
     * @throw TaskException if core or knowledge base are not connected, if skill with name id s does not exist in this task, or if the skill
     * has been terminated by a non-nominal event.
     */
    template<typename T>void execute_skill(const std::string &skill_id){
        if(m_context["skills"].find(skill_id)==m_context["skills"].end()){
            spdlog::error("Skill with id "+skill_id+" not in this task. Check the task context for consistency. Stopping task.");
            this->abort_task();
            throw TaskException("Skill with id "+skill_id+" not in this task. Check the task context for consistency. Stopping task.");
        }
        if(m_flag_stop){
            return;
        }
        std::shared_ptr<Skill> skill = std::make_shared<T>(skill_id,m_memory,m_context[skill_id],m_core->get_percept());
        if(!m_core->load_skill(skill)){
            throw TaskException("Skill could not be loaded into core.");
        }
        spdlog::info("Executing skill "+skill_id+".");
        m_core->execute_skill();
        m_core->unload_skill();
        skill->terminate();
        m_result.m_skill_results.insert(std::make_pair(skill_id,skill->get_eval()));
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

    void write_result(bool success,double cost_suc,double cost_err,nlohmann::json custom_results);


private:

    /**
     * Checks the task description for syntax errors. Returns false if necessary elements are missing or if additional invalids ones are present.
     * @param[in] descr The task description to check.
     * @return True if the given task description is valid, false otherwise.
     */
    bool check_context(const nlohmann::json& default_context, const nlohmann::json &user_context) const;
    static std::string generate_uuid() const;

    nlohmann::json m_context;
    TaskResult m_result;

    std::unordered_set<std::string> m_reserved_skills;
    std::unordered_set<std::string> m_reserved_subtasks;

    std::atomic<bool> m_flag_stop;
    std::atomic<bool> m_flag_recover;
    std::atomic<bool> m_flag_in_recovery;
    Core* m_core;
    Memory* m_memory;

    std::string m_state;

    const std::string m_id;
    const std::string m_uuid;

    std::set<std::shared_ptr<TaskObserver> > m_observers;

};

}
