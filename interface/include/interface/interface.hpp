#pragma once

#include <memory>
#include <nlohmann/json.hpp>

namespace mios {
class Core;
class TaskEngine;
class Portal;
class Memory;

class CommandInterface{
public:
    CommandInterface(Core *core, TaskEngine *task_engine, Portal *portal, Memory* memory);
private:
    void bind_methods();

    nlohmann::json start_task(const nlohmann::json& request);
    nlohmann::json stop_task(const nlohmann::json& request);
    nlohmann::json remove_task(const nlohmann::json& request);
    nlohmann::json wait_for_task(const nlohmann::json& request);
    nlohmann::json is_busy(const nlohmann::json& request);

    nlohmann::json post_event(const nlohmann::json& request);
    nlohmann::json get_event(const nlohmann::json& request);

    nlohmann::json set_grasped_object(const nlohmann::json& request);
    nlohmann::json grasp_object(const nlohmann::json& request);
    nlohmann::json grasp(const nlohmann::json& request);
    nlohmann::json release_object(const nlohmann::json& request);
    nlohmann::json move_gripper(const nlohmann::json& request);
    nlohmann::json home_gripper(const nlohmann::json& request);

    // knowledge base level
    nlohmann::json teach_object(const nlohmann::json& request);
    nlohmann::json set_partial_object_data(const nlohmann::json& request);
    nlohmann::json set_object(const nlohmann::json& request);
    nlohmann::json apply_reference_frame(const nlohmann::json& request);
    nlohmann::json download_task_context(const nlohmann::json& request);
    nlohmann::json download_skill_context(const nlohmann::json& request);
    nlohmann::json download_object_context(const nlohmann::json& request);

    // info level
    nlohmann::json get_state(const nlohmann::json& request);
    nlohmann::json get_model(const nlohmann::json& request);

    // robot level
    nlohmann::json start_desk_task(const nlohmann::json& request);
    nlohmann::json stop_desk_task(const nlohmann::json& request);
    nlohmann::json unlock_brakes(const nlohmann::json& request);
    nlohmann::json lock_brakes(const nlohmann::json& request);
    nlohmann::json shutdown(const nlohmann::json& request);
    nlohmann::json pack_pose(const nlohmann::json& request);

    nlohmann::json set_live_parameter(const nlohmann::json& request);

    nlohmann::json terminate(const nlohmann::json& request);

    nlohmann::json learn_task(const nlohmann::json& request);
    nlohmann::json stop_learning(const nlohmann::json& request);

private:
    Core* m_core;
    TaskEngine* m_task_engine;
    Portal* m_portal;
    Memory* m_memory;
};


}
