#pragma once

#include <list>
#include <map>
#include <atomic>

#include "manipulation_primitive/manipulation_primitive.hpp"
#include "knowledge_base/local_memory.hpp"
#include "knowledge_base/knowledge_base.hpp"
#include "knowledge_base/concepts.hpp"

#include "cpp_utils/conversion.hpp"
#include "cpp_utils/files.hpp"
#include "cpp_utils/json.hpp"
#include "cpp_utils/math.hpp"
#include "cpp_utils/output.hpp"


namespace mios {


const static std::set<std::string> global_skill_parameters={"time_max,w_cost_function,parallels_frequency"};

/**
 * The base struct for the skill configuration defines common parameters for all skills.
 */
struct ConfigSkill{
    ConfigSkill(){
        this->time_max=0;
        this->w_cost_function.resize(10);
        this->w_cost_function[0]=1;
        this->parallels_frequency=1;

        this->k_h_p.setZero();
        this->k_h_d.setZero();
    }

    ConfigFrames frames;
    ConfigGeneral general;
    ConfigUser user;
    ConfigLimits limits;
    ConfigSystem system;

    /**
     * Controller configuration.
     */
    ConfigController controller;

    /**
     * Mapping of skill objects to objects in the knowledge base.
     */
    std::map<std::string,std::string> objects;

    /**
     * Maximum time for skill execution. After exceeding this time the skill is terminated unsuccessful. A value of 0 allows for infinite execution time.
     */
    double time_max;

    /**
     * Id to select a custom cost function.
     */
    std::vector<double> w_cost_function;

    /**
     * Frequency of parallel thread
     */
    unsigned parallels_frequency;

    Eigen::Matrix<double,6,1> k_h_p;
    Eigen::Matrix<double,6,1> k_h_d;
};

/**
 * The evaluation struct contains quality metrics for the skill execution and further meta information.
 */
struct EvalSkill{
    EvalSkill(){
        this->config=nullptr;
        this->cost_suc=0;
        this->cost_err=0;
        this->success=false;
        this->last_errors.resize(0);
        this->results=nlohmann::json();
    }

    /**
     * Pointer to the skill configuration.
     */
    std::shared_ptr<ConfigSkill> config;

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

    /**
     * Lists the last thrown exceptions.
     */
    std::vector<std::string> last_errors;

    nlohmann::json results;

};


/**
 * The output struct for a skill. It contains all possible commands and takes care of limiting and buffering.
 */
struct CmdSkill{
    CmdSkill();

    /**
     * Reads the output from a manipulation primitive.
     * @param[in] in The output of a manipulation primitive.
     */
    void read_mp_cmd(const CmdMP& cmd);

    /**
     * Sets all velocity, torque and force commands to zero.
     * @param[in] p Current percept.
     */
    void stop(const Percept &p);

    /**
     * Sets the current skill command to the value in the buffer.
     */
    void read_from_buffer();

    /**
     * Limits the output according to the global settings.
     * @param[in] config Pointer to the global configuration.
     */
    void limit_output(const ConfigLimits& config);

    /**
     * Limits the rate of the output according to the global settings.
     * @param[in] config Pointer to the global configuration.
     */
    void limit_output_rate(const ConfigLimits& config);

    /**
     * Sets initial values for the output.
     * @param[in] p Percept struct.
     */
    void set_0(const Percept& p);

    /**
     * Resets all outputs and buffers. Is called once at instantiation of a skill.
     */
    void reset();

    bool validity_check();

    /**
     * Desired Cartesian pose in task frame.
     */
    Eigen::Matrix<double,4,4> TF_T_EE_d;

    /**
     * Desired Cartesian twist in task frame.
     */
    Eigen::Matrix<double,6,1> TF_dX_d;

    /**
     * Desired Cartesian wrench in task frame. Is passed to the force controller.
     */
    Eigen::Matrix<double,6,1> TF_F_d;

    /**
     * Cartesian feed forward wrench in task frame.
     */
    Eigen::Matrix<double,6,1> TF_F_ff;

    /**
     * Cartesian stiffness.
     */
    Eigen::Matrix<double,6,1> K_x;

    /**
     * Cartesian damping factor.
     */
    Eigen::Matrix<double,6,1> xi_x;

    /**
     * Desired joint pose.
     */
    Eigen::Matrix<double,7,1> q_d;

    /**
     * Desired joint velocities.
     */
    Eigen::Matrix<double,7,1> dq_d;

    /**
     * Desired joint torques.
     */
    Eigen::Matrix<double,7,1> tau_d;

    /**
     * Feed forward joint torques.
     */
    Eigen::Matrix<double,7,1> tau_ff;

    /**
     * Joint stiffness.
     */
    Eigen::Matrix<double,7,1> K_theta;

    /**
     * Joint damping factor.
     */
    Eigen::Matrix<double,7,1> xi_theta;

    bool on_cntrl_imp;
    bool on_cntrl_force;

    Eigen::Matrix<double,4,4> TF_T_EE_d_buffer;
    Eigen::Matrix<double,6,1> TF_dX_d_buffer;
    Eigen::Matrix<double,6,1> TF_F_d_buffer;
    Eigen::Matrix<double,6,1> TF_F_ff_buffer;
    Eigen::Matrix<double,6,1> K_x_buffer;
    Eigen::Matrix<double,6,1> xi_x_buffer;

    Eigen::Matrix<double,7,1> q_d_buffer;
    Eigen::Matrix<double,7,1> dq_d_buffer;
    Eigen::Matrix<double,7,1> tau_d_buffer;
    Eigen::Matrix<double,7,1> tau_ff_buffer;
    Eigen::Matrix<double,7,1> K_theta_buffer;
    Eigen::Matrix<double,7,1> xi_theta_buffer;

    Eigen::Matrix<double,4,4> TF_T_EE_d_limiter;
    Eigen::Matrix<double,6,1> TF_dX_d_limiter;
    Eigen::Matrix<double,6,1> TF_F_d_limiter;
    Eigen::Matrix<double,6,1> TF_F_ff_limiter;
    Eigen::Matrix<double,6,1> K_x_limiter;
    Eigen::Matrix<double,6,1> xi_x_limiter;

    Eigen::Matrix<double,7,1> q_d_limiter;
    Eigen::Matrix<double,7,1> dq_d_limiter;
    Eigen::Matrix<double,7,1> tau_d_limiter;
    Eigen::Matrix<double,7,1> tau_ff_limiter;
    Eigen::Matrix<double,7,1> K_theta_limiter;
    Eigen::Matrix<double,7,1> xi_theta_limiter;

    bool flag_stop;

};

/**
 * The skill base class provides handling of manipulation primitives, error handling and more. Every skill inherits from this class.
 */
class Skill{
public:
    /**
     * The skill base constructor. It is called by the constructor of any derived skill class.
     * @param[in] type The type id of the skill.
     */
    Skill(const std::string& type);

    /**
     * The skill destructor.
     */
    virtual ~Skill();

    /**
     * Resets all flags and containers of the skill and its evaluation struct.
     */
    void reset();

    /**
     * Initializes the skill by building the manipulation primitives, calculating the task frame, preparing the output struct
     * and making validity checks.
     * @param[in] p Percept struct.
     * @return Returns true if initialization was successful, false otherwise.
     */
    bool initialize(const Percept &p);

    void write_O_R_TF(const Percept& p);

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
    const CmdSkill &cycle(const Percept& p);

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
     * Stops the skill.
     */
    void stop_skill();

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
    const EvalSkill& get_eval() const;

    /**
     * Returns a pointer to the configuration struct of this skill. It is explicitly allowed to modify the struct.
     * @return A pointer to the configuratin struct of this skill.
     */
    template<typename T=ConfigSkill>std::shared_ptr<T> get_config() const{
        if(this->_config==nullptr){
            throw SkillException("Skill config is not being created for skill "+this->_type+".");
        }
        return std::static_pointer_cast<T>(this->_config);
    }

    /**
     * Sets the instance id for the skill. Will be removed in future updates.
     * @param[in] id Intended instance id.
     */
    void set_id(const std::string& id);

    /**
     * Connects the knowledge base to the skill.
     * @param[in] kb Pointer to knowledge base.
     */
    void set_kb(std::shared_ptr<KnowledgeBase> kb);

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

    /**
     * Returns the termination flag of the skill that indicates whether the skill has been terminated.
     * @return Returns the termination flag.
     */
    bool get_flag_terminate() const;

    void read_configuration(const nlohmann::json & p);

    /**
     * Reads common skill parameters into the local configuration struct.
     * @param[in] p Common skill parameters in json format.
     */
    void read_global_skill_parameters(const nlohmann::json& p);

    /**
     * Reads specific skill parameters into the local configuration struct. This function has to be defined by the skill developer.
     * It can return a bool to indicate invalid parameter settings.
     * @param[in] p Specific skill parameters in json format.
     * @return Has to be defined by developer. False aborts skill execution.
     */
    virtual bool read_skill_parameters(const nlohmann::json& p) = 0;

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

    /**
     * Needs to be defined by the developer. Has to contain the line "this->_config = new <SkillConfig>();" where <SkillConfig> needs to be
     * replaced by the derived configuration struct.
     */
    virtual void create_config() = 0;
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
    virtual void build_primitives(const Percept& p) = 0;

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
    template<typename T>void insert_mp(const std::string& id, const Percept &p){
        if(this->_mp.find(id)!=this->_mp.end()){
            throw SkillException("Could not insert new manipulation primitive. MP with id "+id+" already exists.");
        }else{
            this->_mp.insert(std::pair<std::string,std::shared_ptr<ManipulationPrimitive> >(id,std::make_shared<T>()));
            this->_mp[id]->set_id(id);
            this->_mp[id]->set_kb((this->_kb));
            this->_mp[id]->get_attractor()->reset();
            this->_mp[id]->init_attractor(p,std::make_shared<ConfigUser>(this->_config->user));
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

    std::shared_ptr<ConfigSkill> _config;
    EvalSkill _eval;

    std::shared_ptr<ManipulationPrimitive> _active_mp;
    std::shared_ptr<KnowledgeBase> _kb;

    CmdSkill _cmd;
private:

    void run_parallels();
    void terminate_parallels();

    std::map<std::string,std::shared_ptr<ManipulationPrimitive> > _mp;
    std::map<std::string,std::shared_ptr<ManipulationPrimitive> > _mp_graph;
    std::string _init_mp;

    std::map<std::string,Object> _objects;


    double _time_start;

    std::atomic<bool> _flag_init;
    std::atomic<bool> _flag_terminate;
    std::atomic<bool> _flag_aborted;
    std::atomic<bool> _flag_invoke_failure;
    std::atomic<bool> _flag_invoke_success;
    std::atomic<bool> _flag_fade_out;
    std::atomic<bool> _flag_success;
    std::atomic<bool> _flag_pause;
    std::atomic<bool> _flag_parallels_running;
    std::atomic<bool> _flag_run_parallels;

    std::string _id;
    std::string const _type;

    std::thread _thr_parallels;

};

}
