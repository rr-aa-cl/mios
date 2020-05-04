#pragma once

#include <memory>
#include <nlohmann/json.hpp>
namespace msrm_utils{
class JsonWebsocketServer;
}
namespace mios {
class Core;
class TaskHandler;

class Interface{
public:
    Interface();
    ~Interface();

    void initialize(std::shared_ptr<Core> core, std::shared_ptr<TaskHandler> task_handler, unsigned port);
    void start();
    void stop();

private:
    void bind_methods();

    nlohmann::json start_task(const nlohmann::json& request);
    nlohmann::json stop_task(const nlohmann::json& request);
    nlohmann::json remove_task(const nlohmann::json& request);
    nlohmann::json wait_for_task(const nlohmann::json& request);
    nlohmann::json check_if_task_finished(const nlohmann::json& request);
    nlohmann::json is_busy(const nlohmann::json& request);

    nlohmann::json subscribe_to_event_stream(const nlohmann::json& request);
    nlohmann::json unsubscribe_from_event_stream(const nlohmann::json& request);

    nlohmann::json set_grasped_object(const nlohmann::json& request);
    nlohmann::json grasp_object(const nlohmann::json& request);
    nlohmann::json grasp(const nlohmann::json& request);
    nlohmann::json release_object(const nlohmann::json& request);
    nlohmann::json move_gripper(const nlohmann::json& request);
    nlohmann::json home_gripper(const nlohmann::json& request);

    nlohmann::json lockdown_core(const nlohmann::json& request);
    nlohmann::json lift_core_lockdown(const nlohmann::json& request);

    // skill level
    nlohmann::json set_skill_pause_state(const nlohmann::json& request);

    // knowledge base level
    nlohmann::json teach_object(const nlohmann::json& request);
    nlohmann::json apply_reference_frame(const nlohmann::json& request);
    nlohmann::json download_task_description(const nlohmann::json& request);
    nlohmann::json download_skill_description(const nlohmann::json& request);
    nlohmann::json download_object_description(const nlohmann::json& request);

    // info level
    nlohmann::json get_state(const nlohmann::json& request);

    nlohmann::json login_digital_twin(const nlohmann::json& request);
    nlohmann::json logout_digital_twin(const nlohmann::json& request);

    // global level
    nlohmann::json reset(const nlohmann::json& request);

    // robot level
    nlohmann::json unlock_brakes(const nlohmann::json& request);
    nlohmann::json lock_brakes(const nlohmann::json& request);
    nlohmann::json shutdown(const nlohmann::json& request);
    nlohmann::json pack_pose(const nlohmann::json& request);


    std::shared_ptr<msrm_utils::JsonWebsocketServer> _ws_server;

    std::shared_ptr<Core> _core;
    std::shared_ptr<TaskHandler> _task_handler;
};


}
