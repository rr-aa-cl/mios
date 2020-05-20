#pragma once

#include <list>
#include <map>
#include <atomic>

#include "manipulation_primitive/manipulation_primitive.hpp"
#include "memory/memory.hpp"

#include "data_structures/percept.hpp"
#include "data_structures/actuator.hpp"
#include "data_structures/parameters.hpp"


namespace mios {

/**
 * The evaluation struct contains quality metrics for the skill execution and further meta information.
 */
class SkillResult{
    SkillResult();

    /**
     * Pointer to the skill configuration.
     */
    std::shared_ptr<SkillParameters> config;

    /**
     * Map that contains the percept struct at the beginning of execution of each manipulation primitive of the skill.
     * The key is the name of the respective primitive.
     */
    std::map<std::string,Percept> percepts;

    /**
     * Percept struct at the beginning of skill execution.
     */
    Percept p_0;

    /**
     * Percept struct at the end of skill execution.
     */
    Percept p_1;

    /**
     * Cost of skill execution in case of success.
     */
    double cost_suc;

    /**
     * Cost of skill execution in case of failure.
     */
    double cost_err;

    /**
     * Additional inquality constraints. The key is the constraint's identifier, the value the constraint in implicit form.
     */
    std::map<std::string,double> constraints;

    /**
     * Indicates whether the skill execution was successful.
     */
    bool success;

    bool exception;

    /**
     * Lists the last thrown exceptions.
     */
    std::vector<std::string> last_errors;

    nlohmann::json results;

};


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
    Skill(const std::string& type, Memory *memory, std::shared_ptr<SkillParameters> config, const Percept& p);

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

    void write_O_R_TF_to_config(const Percept& p);

    /**
     * Calculates O_R_TF for this skill. It can be static, provided in the task description or based on the percept at time of skill execution.
     * @param[in] p Percept struct.
     * @return Return O_R_TF to be used for this skill. Return the 0 matrix to use the values from the task description.
     */
    virtual Eigen::Matrix<double,3,3> get_O_R_TF(const Percept& p);

    /**
     * Main execution loop of the skill. Manages all manipulation primitives, local and global conditions.
     * @param[in] p Percept struct.
     * @return Output of the skill.
     */
    Actuator *cycle(const Percept& p);

    /**
     * Is called at the end of skill execution. Terminates manipulation primitives and calls the evaluate function.
     */
    void terminate();

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
    SkillResult get_eval() const;

    /**
     * Returns a pointer to the configuration struct of this skill. It is explicitly allowed to modify the struct.
     * @return A pointer to the configuratin struct of this skill.
     */
    template<typename T=SkillParameters>std::shared_ptr<T> get_config() const{
        return std::static_pointer_cast<T>(m_config);
    }

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
    void set_object(const std::string& o_type, const std::string& o);
    void set_object(const std::string& o_type, const Object& o);

    /**
     * Loads skill object from the skill description and maps them to objects in the knowledge base as defined by the task description.
     * @param[in] object_types Skill objects in json format.
     * @param[in] objects Objects in knowledge base in json format.
     * @return Returns false if objects are invalid.
     */
    bool load_objects(const std::map<std::string, std::string> &objects);

    /**
     * Returns a const reference to the indicated skill object.
     * @param[in] o Id of skill object.
     * @return A const reference to object.
     *
     * @throw SkillException if o is not a skill object.
     */
    const Object &get_object(const std::string& o) const;


    /**
     * Returns pose of object.
     * @param o Id of skill object.
     * @param TF Determines whether the pose should be given in task frame or base frame.
     * @return Object pose.
     */
    Eigen::Matrix<double,4,4> get_object_pose(const std::string& o, bool TF=true);

    /**
     * To be defined by developer. This function sets up the evaluation struct based on the skill execution.
     */
    virtual void evaluate() = 0;
protected:

    /**
     * Returns a pointer to the specified manipulation primitive.
     * @param[in] mp Id of manipulation primitive.
     * @return Pointer to manipulation primitive with id mp.
     *
     * @throw SkillException if mp does not exist in this skill.
     */
    std::shared_ptr<ManipulationPrimitive> get_mp(const std::string& mp) const;

    /**
     * This function needs to be defined by the developer. It contains the setup of all manipulation primitives.
     * @param[in] p Percept struct.
     */
    virtual bool build_primitives(const Percept& p) = 0;

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
    void set_init_mp(const std::string& id);

    /**
     * Creates manipulation primitive.
     * @param[in] id Id of the manipulation primitive.
     * @param[in] mp Pointer to manipulation primitive object. Implicit creation is recommended.
     * @param[in] p Percept struct.
     * @param[in] c Pointer to global configuration struct of the skill.
     *
     * @throw SkillException if manipulation primitive with id already exists.
     */
    template<typename T_primitive,typename T_config,typename T_attractor>void insert_mp(const std::string& id, const Percept &p){
        if(m_mp_graph.find(id)!=m_mp_graph.end()){
            throw SkillException("Could not insert new manipulation primitive. MP with id "+id+" already exists.");
        }else{
            m_mp_graph.insert(std::pair<std::string,std::shared_ptr<ManipulationPrimitive> >(id,std::make_shared<T_primitive>(p,std::make_shared<T_config>(),
                                                                                                                      std::make_shared<T_attractor>(),m_memory,id)));
        }
    }

    /**
     * Checks global error conditions that hold for any skill. These are violations of maximum external wrench or joint torques, maximum execution time or
     * external trigger.
     * @param[in] p Percept struct.
     * @return True if global error conditions have been violated, false otherwise.
     *
     * @throw SkillException if configuration struct has not been set by developer via the function "create_config".
     */
    bool check_global_err_conditions(const Percept& p);

    /**
     * Checks global success conditions that hold for any skill. These are external trigger.
     * @param[in] p Percept struct.
     * @return True if global success conditions have been fulfilled, false otherwise.
     */
    bool check_global_suc_conditions(const Percept& p) const;

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

    /**
     * This function checks the transitions of the MP graph. It is user-defined and needs to check for every MP (a node in the graph)
     * if it may switch to another MP.
     * @param[in] p Percept struct.
     * @return A tuple consisting of a bool (to indicate whether to trigger a transition) and a string that is the id of the successor MP if the transition is activated.
     */
    virtual std::tuple<bool,std::string> check_edges(const Percept& p) = 0;

    /**
     * This function runs as a parallel thread at a specified frequency.
     */
    virtual void parallels();

    double get_t_init() const;


    std::shared_ptr<ManipulationPrimitive> m_active_mp;
    Memory* m_memory;

private:
    SkillResult m_result;

    void run_parallels();
    void terminate_parallels();
    bool has_settled();

    std::map<std::string,std::shared_ptr<ManipulationPrimitive> > m_mp_graph;
    std::string m_init_mp;

    std::map<std::string,Object> m_objects;


    double m_time_start;

    std::atomic<bool> m_flag_invoke_failure;
    std::atomic<bool> m_flag_invoke_success;
    std::atomic<bool> m_flag_pause;
    std::atomic<bool> m_flag_parallels_running;
    std::atomic<bool> m_flag_run_parallels;

    std::string m_id;
    std::string const m_type;

    std::thread m_thr_parallels;
    SkillLifeCycle m_life_cycle;

};

}
