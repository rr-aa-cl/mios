#pragma once

#include <iostream>
#include <map>
#include <functional>
#include <thread>

#include <simple-websocket-server/server_ws.hpp>

#include <msrm_utils/json.hpp>

#include "core/core.hpp"
#include "task/task_handler.hpp"

namespace mios {


class WSServer{
public:
    WSServer(std::string address, unsigned port);
    ~WSServer();

    void setup(Core* core, TaskHandler* task_handler);

    void start_listening();
    void stop();

    void bind_method(std::string name, std::function<nlohmann::json(const nlohmann::json& request)> method, std::set<std::string> arguments);
private:

    nlohmann::json start_task(const nlohmann::json& request);
    nlohmann::json stop_task(const nlohmann::json& request);
    nlohmann::json remove_task(const nlohmann::json& request);
    nlohmann::json wait_for_task(const nlohmann::json& request);
    nlohmann::json check_if_task_finished(const nlohmann::json& request);
    nlohmann::json is_busy(const nlohmann::json& request);

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


    std::pair<bool, std::string> message_preprocessing(nlohmann::json &message);
    bool check_if_method_known(std::string method);
    bool check_arguments(const nlohmann::json& request, const std::set<std::string> &arguments, nlohmann::json& response);

    SimpleWeb::SocketServer<SimpleWeb::WS> _server;
    std::map<std::string, std::function<nlohmann::json(nlohmann::json)> > _methods;
    std::map<std::string, std::set<std::string> > _arguments;

    Core* _core;
    TaskHandler* _task_handler;

    std::thread _thread;

};

}
