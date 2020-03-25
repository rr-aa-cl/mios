#pragma once

#include <string>

#include <jsonrpccxx/server.hpp>
#include <nlohmann/json.hpp>

#include "cpp_utils/output.hpp"

namespace mios {

class Core;
class TaskHandler;

class RPCServer{
public:
    RPCServer(jsonrpccxx::JsonRpc2Server &rpc_server);
    ~RPCServer();

    void setup(Core* core, TaskHandler* task_handler);

private:
    // task level
    nlohmann::json start_task(const std::string task, const bool queue, const nlohmann::json& parameters);
    nlohmann::json stop_task(const bool nominal, const bool success, const bool recover, const bool empty_queue, const double cost_suc, const double cost_err);
    nlohmann::json remove_task(const std::string task_uuid);
    nlohmann::json wait_for_task(const std::string task_uuid);
    nlohmann::json check_if_finished(const std::string task_uuid);
    nlohmann::json is_busy();

    nlohmann::json set_grasped_object(std::string object);
    nlohmann::json grasp_object(std::string object, const double width, const double speed, const double force, const bool check_width);
    nlohmann::json grasp(double width, double speed, double force);
    nlohmann::json release_object(double width, double speed);
    nlohmann::json move_gripper(double width, double speed);
    nlohmann::json home_gripper();

    nlohmann::json lockdown_core();
    nlohmann::json lift_core_lockdown();

    // skill level
    nlohmann::json set_skill_pause_state(bool pause);

    // knowledge base level
    nlohmann::json teach_object(const std::string object, const bool teach_width, const std::string reference_frame, const bool is_reference_frame);
    nlohmann::json apply_reference_frame(const std::string frame);
    nlohmann::json download_task_description(const std::string task);
    nlohmann::json download_skill_description(const std::string skill);
    nlohmann::json download_object_description(const std::string object);

    // info level
    nlohmann::json get_state();

    nlohmann::json login_digital_twin();
    nlohmann::json logout_digital_twin();

    // global level
    nlohmann::json reset();

    // robot level
    nlohmann::json unlock_brakes();
    nlohmann::json lock_brakes();
    nlohmann::json shutdown();
    nlohmann::json pack_pose();

    jsonrpccxx::JsonRpc2Server* _rpc_server;
    Core* _core;
    TaskHandler* _task_handler;

};

}
