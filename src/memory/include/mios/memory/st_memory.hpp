#pragma once


#include "mios/data_structures/parameters.hpp"
#include "mios/data_structures/task_data.hpp"
#include "mios/data_structures/object.hpp"
#include "mios/data_structures/percept.hpp"
#include "mios/data_structures/event.hpp"

#include "nlohmann/json.hpp"

#include <optional>
#include <mutex>
#include <string>
#include <unordered_map>

namespace mios {

class LTMemory;

class STMemory{
public:
    STMemory();
    bool initialize();
    bool is_ok() const;
    void link_to_lt_memory(LTMemory* lt_memory);
    bool syncronize_with_lt_memory();

    bool apply_skill_context(const nlohmann::json task_context, const std::string& skill_id);
    bool apply_reserved_skill_context(const std::string& skill_id);
    bool update_object(const std::string& name, bool teach_width, double teach_force, const Percept& p);
    bool update_object(const std::string& name, const nlohmann::json& description);
    bool update_partial_object(const std::string& name, const nlohmann::json& description);

    void internal_update(const Percept& p);

    void clear_reserved_skills();
    void clear_skill_parameters();

    template<typename T>bool reserve_skill_context(const nlohmann::json task_context, const std::string& skill_id){
        Parameters p=m_parameters;
        p.create_skill_parameters<T>();
        if(m_reserved_parameters.find(skill_id)!=m_reserved_parameters.end()){
            return false;
        }
        m_reserved_parameters.insert(std::pair<std::string,Parameters>(skill_id,p));
        if(!reserve_parameters(task_context,skill_id)){
            return false;
        }
        return true;
    }

public:
    bool set_default_parameters();
    void put_task(const std::string& name, const nlohmann::json& context, const TaskResult& result);
    void put_subtask(const std::string& name, const nlohmann::json& context);
    void set_live_parameter(const std::string& key, const nlohmann::json& value);
    void post_event(const std::string& name, const nlohmann::json& content);
    void remove_event(const std::string& name);

public:
    LiveContext* get_live_context();
    Parameters* get_parameters();
    const Parameters* read_parameters() const;
    const TaskData* get_task_data() const;
    std::optional<nlohmann::json> get_live_parameter(const std::string& parameter);
    Object *get_object(const std::string& name);
    const Event* get_event(const std::string& name) const;
    const std::unordered_map<std::string, Object>* get_environment() const;

private:
    bool reserve_parameters(const nlohmann::json task_context, const std::string &skill_id);
    void merge_live_context();

private:
    std::mutex m_mtx_live_context;
    std::unordered_map<std::string,Object> m_environment;
    std::unordered_map<std::string,Event> m_events;
    LiveContext m_live_context;
    Parameters m_parameters;

    std::unordered_map<std::string,Parameters> m_reserved_parameters;

    LTMemory* m_lt_memory;

};

}
