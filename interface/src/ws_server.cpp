#include "interface/ws_server.hpp"

namespace mios {

WSServer::WSServer(std::string address, unsigned port){
    this->_server.config.address=address;
    this->_server.config.port=port;
    this->_server.config.thread_pool_size=10;

    auto &echo = this->_server.endpoint["^/mios/?$"];

    echo.on_message = [this](std::shared_ptr<SimpleWeb::SocketServer<SimpleWeb::WS>::Connection> connection, std::shared_ptr<SimpleWeb::SocketServer<SimpleWeb::WS>::InMessage> message_raw) {

        nlohmann::json message, response;
        try{
//            std::cout<<"MESSAGE: "<<message_raw->string()<<std::endl;
            message = nlohmann::json::parse(message_raw->string());
            std::pair<bool,std::string> result=this->message_preprocessing(message);
            if(result.first){
                std::string method;
                message["method"].get_to(method);
                if(!this->check_if_method_known(method)){
                    response["result"]="Method " + method + " not known.";
                }else{
                    if(this->check_arguments(message["request"],this->_arguments[method],response)){
                        response["result"]=this->_methods[method](message["request"]);
                    }
                }
            }else{
                response["result"]=result.second;
            }
        }catch(const nlohmann::detail::type_error& e){
            std::cout<<e.what()<<std::endl;
            response["result"]=e.what();
        }catch(const nlohmann::detail::parse_error& e){
            std::cout<<e.what()<<std::endl;
            response["result"]=e.what();
        }
        auto out_message = response.dump();

        // connection->send is an asynchronous function
        connection->send(out_message, [](const SimpleWeb::error_code &ec) {
            if(ec) {
                std::cout << "Server: Error sending message. " <<
                             // See http://www.boost.org/doc/libs/1_65_0/doc/html/boost_asio/reference.html, Error Codes for error code meanings
                             "Error: " << ec << ", error message: " << ec.message() << std::endl;
            }
        });
    };

    echo.on_open = [](std::shared_ptr<SimpleWeb::SocketServer<SimpleWeb::WS>::Connection> connection) {
//        std::cout << "Server: Opened connection " << connection.get() << std::endl;
    };

    // See RFC 6455 7.4.1. for status codes
    echo.on_close = [](std::shared_ptr<SimpleWeb::SocketServer<SimpleWeb::WS>::Connection> connection, int status, const std::string & /*reason*/) {
//        std::cout << "Server: Closed connection " << connection.get() << " with status code " << status << std::endl;
    };

    // Can modify handshake response headers here if needed
    echo.on_handshake = [](std::shared_ptr<SimpleWeb::SocketServer<SimpleWeb::WS>::Connection> /*connection*/, SimpleWeb::CaseInsensitiveMultimap & /*response_header*/) {
        return SimpleWeb::StatusCode::information_switching_protocols; // Upgrade to websocket
    };

    // See http://www.boost.org/doc/libs/1_55_0/doc/html/boost_asio/reference.html, Error Codes for error code meanings
    echo.on_error = [](std::shared_ptr<SimpleWeb::SocketServer<SimpleWeb::WS>::Connection> connection, const SimpleWeb::error_code &ec) {
        std::cout << "Server: Error in connection " << connection.get() << ". "
                  << "Error: " << ec << ", error message: " << ec.message() << std::endl;
    };
}

WSServer::~WSServer(){

}

void WSServer::setup(Core *core, TaskHandler *task_handler){
    this->_core=core;
    this->_task_handler=task_handler;
    this->bind_method("start_task",boost::bind(&WSServer::start_task,this,_1),{"task","parameters","queue"});
    this->bind_method("stop_task",boost::bind(&WSServer::stop_task,this,_1),{"nominal","success","recover","empty_queue","cost_suc","cost_err"});
    this->bind_method("remove_task",boost::bind(&WSServer::remove_task,this,_1),{"task_uuid"});
    this->bind_method("wait_for_task",boost::bind(&WSServer::wait_for_task,this,_1),{"task_uuid"});
    this->bind_method("check_if_task_finished",boost::bind(&WSServer::check_if_task_finished,this,_1),{"task_uuid"});
    this->bind_method("is_busy",boost::bind(&WSServer::is_busy,this,_1),{"task_uuid"});

    this->bind_method("set_grasped_object",boost::bind(&WSServer::set_grasped_object,this,_1),{"object"});
    this->bind_method("grasp_object",boost::bind(&WSServer::grasp_object,this,_1),{"object","width","speed","force","check_width"});
    this->bind_method("grasp",boost::bind(&WSServer::grasp,this,_1),{"width","speed","force"});
    this->bind_method("release_object",boost::bind(&WSServer::release_object,this,_1),{"width","speed"});
    this->bind_method("move_gripper",boost::bind(&WSServer::move_gripper,this,_1),{"width","speed"});
    this->bind_method("home_gripper",boost::bind(&WSServer::home_gripper,this,_1),{});

    this->bind_method("lockdown_core",boost::bind(&WSServer::lockdown_core,this,_1),{});
    this->bind_method("lift_core_lockdown",boost::bind(&WSServer::lift_core_lockdown,this,_1),{});

    this->bind_method("set_skill_pause_state",boost::bind(&WSServer::lift_core_lockdown,this,_1),{"pause"});

    this->bind_method("teach_object",boost::bind(&WSServer::teach_object,this,_1),{"object","teach_width","reference_frame","is_reference_frame"});
    this->bind_method("apply_reference_frame",boost::bind(&WSServer::apply_reference_frame,this,_1),{"frame"});
    this->bind_method("download_task_description",boost::bind(&WSServer::download_task_description,this,_1),{"task"});
    this->bind_method("download_skill_description",boost::bind(&WSServer::download_skill_description,this,_1),{"skill"});
    this->bind_method("download_object_description",boost::bind(&WSServer::download_object_description,this,_1),{"object"});

    this->bind_method("get_state",boost::bind(&WSServer::get_state,this,_1),{});

    this->bind_method("login_digital_twin",boost::bind(&WSServer::login_digital_twin,this,_1),{});
    this->bind_method("logout_digital_twin",boost::bind(&WSServer::logout_digital_twin,this,_1),{});

    this->bind_method("reset",boost::bind(&WSServer::reset,this,_1),{});

    this->bind_method("unlock_brakes",boost::bind(&WSServer::unlock_brakes,this,_1),{});
    this->bind_method("lock_brakes",boost::bind(&WSServer::lock_brakes,this,_1),{});
    this->bind_method("shutdown",boost::bind(&WSServer::shutdown,this,_1),{});
    this->bind_method("pack_pose",boost::bind(&WSServer::pack_pose,this,_1),{});

}

void WSServer::start_listening(){
    this->_thread = std::thread([this]() {
        // Start server
        this->_server.start();
    });
}

void WSServer::stop(){
    this->_server.stop();
}

std::pair<bool,std::string> WSServer::message_preprocessing(nlohmann::json &message){
    try{
        if(!cpp_utils::find_json_value(message, "method")) return std::pair<bool,std::string>(false,"Message header does not contain <method>.");
        if(!message["method"].is_string()) return std::pair<bool,std::string>(false,"Method is not a readable string.");
        if(!cpp_utils::find_json_value(message,"request")){
            message["request"]=nlohmann::json();
        }
    }catch(const nlohmann::detail::type_error& e){
        std::cout<<e.what()<<std::endl;
        return std::pair<bool,std::string>(false,"Json type error.");
    }
    return std::pair<bool,std::string>(true,"");
}

bool WSServer::check_if_method_known(std::string method){
    if(this->_methods.find(method)==this->_methods.end()){
        return false;
    }else{
        return true;
    }
}

void WSServer::bind_method(std::string name, std::function<nlohmann::json (const nlohmann::json& request)> method,std::set<std::string> arguments){
    this->_methods.insert(std::pair<std::string,std::function<nlohmann::json(const nlohmann::json&)> >(name, method));
    this->_arguments.insert(std::pair<std::string,std::set<std::string> >(name,arguments));
}

bool WSServer::check_arguments(const nlohmann::json &request, const std::set<std::string> &arguments, nlohmann::json &response){
    if(!request.is_object() && !request.is_null()){
        response["result"]="Request must be a json object (can be null).";
        return false;
    }
    for(std::string a : arguments){
        if(!cpp_utils::find_json_value(request,a)){
            response["result"]="Could not find parameter "+a+" in request.";
            return false;
        }
    }
    return true;
}

nlohmann::json WSServer::start_task(const nlohmann::json &request){
    nlohmann::json response;
    std::pair<bool,std::string> result=this->_task_handler->start_task(request["task"],request["parameters"],request["queue"]);
    if(result.first){
        response["task_uuid"]=result.second;
        response["result"]=true;
    }else{
        response["error"]=result.second;
        response["result"]=false;
    }
    return response;
}

nlohmann::json WSServer::stop_task(const nlohmann::json &request){
    nlohmann::json response;
    std::pair<bool,std::string> result;
    result=this->_task_handler->stop_task(request["nominal"],request["success"],request["recover"],request["empty_queue"],request["cost_suc"],request["cost_err"]);
    if(result.first){
        response["result"]=true;
    }else{
        cpp_utils::print_error(result.second);
        response["error"]=result.second;
        response["result"]=false;
    }
    return response;
}

nlohmann::json WSServer::remove_task(const nlohmann::json &request){
    nlohmann::json response;
    std::string task_uuid;
    request["task_uuid"].get_to(task_uuid);

    if(this->_task_handler->get_active_task_id()==task_uuid){
        response["error"]="Cannot remove the currently running task.";
        response["result"]=false;
    }else if(this->_task_handler->has_id(task_uuid)){
        std::pair<bool,std::string> result;
        cpp_utils::print_info("Removing task with uuid " + task_uuid + ".");
        result=this->_task_handler->remove_task(task_uuid);
        if(result.first){
            response["result"]=true;
        }else{
            response["error"]=result.second;
            response["result"]=false;
        }
    }else{
        response["error"]="Task uuid " + task_uuid + " is not known to the task scheduler.";
        response["result"]=false;
    }
    return response;
}

nlohmann::json WSServer::wait_for_task(const nlohmann::json &request){
    nlohmann::json response;
    std::string task_uuid;
    request["task_uuid"].get_to(task_uuid);
    std::pair<EvalTask,bool> e =this->_task_handler->wait_for_task(task_uuid);
    if(e.second==false){
        cpp_utils::print_error("Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.");
        response["error"]="Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.";
        response["result"]=false;
        response["eval"]=nlohmann::json();
        return response;
    }else{
        response["result"]=true;
        nlohmann::json eval;
        eval["success"]=e.first.success;
        eval["cost_err"]=e.first.cost_err;
        eval["cost_suc"]=e.first.cost_suc;
        eval["nominal_termination"]=e.first.nominal_termination;
        eval["results"]=e.first.results;
        eval["error"]=e.first.last_error;
        response["eval"]=eval;
        return response;
    }
}

nlohmann::json WSServer::check_if_task_finished(const nlohmann::json &request){
    nlohmann::json response;
    std::string task_uuid;
    request["task_uuid"].get_to(task_uuid);
    std::pair<EvalTask,bool> e = this->_task_handler->check_if_finished(task_uuid);
    if(e.second==false){
        cpp_utils::print_error("Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.");
        response["error"]="Could not subscribe to task with uuid "+task_uuid+" or find its evaluation in memory.";
        response["finished"]=false;
        response["eval"]=nlohmann::json();
        return response;
    }else{
        response["finished"]=true;
        nlohmann::json eval;
        eval["success"]=e.first.success;
        eval["cost_err"]=e.first.cost_err;
        eval["cost_suc"]=e.first.cost_suc;
        eval["nominal_termination"]=e.first.nominal_termination;
        eval["results"]=e.first.results;
        eval["error"]=e.first.last_error;
        response["eval"]=eval;
        return response;
    }
}

nlohmann::json WSServer::is_busy(const nlohmann::json &request){
    nlohmann::json response;
    response["result"]=true;
    response["busy"]=this->_task_handler->is_busy();
    return response;
}

nlohmann::json WSServer::set_grasped_object(const nlohmann::json &request){
    nlohmann::json response;
    if(!this->_core->set_grasped_object(request["object"])){
        response["result"]=false;
        response["error"]="Could not set grasped object.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json WSServer::grasp_object(const nlohmann::json &request){
    nlohmann::json response;
    if(!this->_core->grasp_object(request["object"],request["width"],request["speed"],request["force"],request["check_width"])){
        response["result"]=false;
        response["error"]="Grasping has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json WSServer::grasp(const nlohmann::json &request){
    nlohmann::json response;
    cpp_utils::print_info("Moving gripper");
    if(!this->_core->grasp(request["width"],request["speed"],request["force"])){
        response["result"]=false;
        response["error"]="Could not move gripper.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json WSServer::release_object(const nlohmann::json &request){
    cpp_utils::print_info("Releasing object");
    nlohmann::json response;
    if(!this->_core->release_object(request["width"],request["speed"])){
        response["result"]=false;
        response["error"]="Releasing has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json WSServer::move_gripper(const nlohmann::json &request){
    nlohmann::json response;
    cpp_utils::print_info("Moving gripper");
    if(!this->_core->move_gripper(request["width"],request["speed"])){
        response["result"]=false;
        response["error"]="Could not move gripper.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json WSServer::home_gripper(const nlohmann::json &request){
    nlohmann::json response;
    if(!this->_core->home_gripper()){
        response["result"]=false;
        response["error"]="Homing has failed.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json WSServer::lockdown_core(const nlohmann::json &request){
    cpp_utils::print_info("Locking core.");
    this->_core->lockdown();
    return nlohmann::json();
}

nlohmann::json WSServer::lift_core_lockdown(const nlohmann::json &request){
    cpp_utils::print_info("Lifting core lockdown.");
    this->_core->lift_lockdown();
    return nlohmann::json();
}

nlohmann::json WSServer::set_skill_pause_state(const nlohmann::json &request){
    nlohmann::json response;
    response["result"]=true;
    this->_core->toggle_skill_pause(request["pause"]);
    return response;
}

nlohmann::json WSServer::teach_object(const nlohmann::json &request){
    nlohmann::json response;
    try{
        const Percept p=this->_core->request_percept(Eigen::Matrix<double,3,3>::Zero(3,3),true);
        if(!this->_core->get_kb()->teach_object(request["object"],p,request["is_reference_frame"],request["reference_frame"],request["teach_width"])){
            response["result"]=false;
            response["error"]="Object can not be teached.";
        }
    }catch(const CoreException& e){
        std::cout<<e.what()<<std::endl;
        response["error"]=e.what();
        response["result"]=false;
    }
    return response;
}

nlohmann::json WSServer::apply_reference_frame(const nlohmann::json &request){
    nlohmann::json response;
    if(!this->_core->get_kb()->apply_reference_frame(request["frame"])){
        response["result"]=false;
        response["error"]="Reference frame could not be applied.";
    }else{
        response["result"]=true;
    }
    return response;
}

nlohmann::json WSServer::download_task_description(const nlohmann::json &request){
    nlohmann::json response, description;
    std::string task;
    request["task"].get_to(task);
    if(this->_core->get_kb()->load_task(task,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download task with name "+task+".";
    }
    return response;
}

nlohmann::json WSServer::download_skill_description(const nlohmann::json &request){
    nlohmann::json response, description;
    std::string skill;
    request["skill"].get_to(skill);
    if(this->_core->get_kb()->load_skill(skill,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download skill with name "+skill+".";
    }
    return response;
}

nlohmann::json WSServer::download_object_description(const nlohmann::json &request){
    nlohmann::json response, description;
    std::string object;
    request["object"].get_to(object);
    if(this->_core->get_kb()->load_object(object,description)){
        response["description"]=description;
        response["result"]=true;
    }else{
        response["result"]=false;
        response["error"]="Could not download task with name "+object+".";
    }
    return response;
}

nlohmann::json WSServer::get_state(const nlohmann::json &request){
    nlohmann::json response;
    try{
        const Percept p = this->_core->request_percept(this->_core->get_kb()->get_local_memory()->access_config_frames().O_R_TF);
        cpp_utils::write_json_array<double,7,1>(response["q"],p.q);
        cpp_utils::write_json_array<double,4,4>(response["O_T_EE"],p.O_T_EE);
        response["active_task"]=p.mios_state.active_task;
        response["result"]=true;
    }catch(const CoreException& e){
        response["error"]=e.what();
        response["result"]=false;
    }
    return response;
}

nlohmann::json WSServer::login_digital_twin(const nlohmann::json &request){
    cpp_utils::print_info("Logging into digital twin.");
    this->_core->login_digital_twin();
    return nlohmann::json();
}

nlohmann::json WSServer::logout_digital_twin(const nlohmann::json &request){
    cpp_utils::print_info("Logging out of digital twin.");
    this->_core->logout_digital_twin();
    return nlohmann::json();
}

nlohmann::json WSServer::reset(const nlohmann::json &request){
    nlohmann::json response;
    this->_task_handler->set_interrupt(true);
    cpp_utils::print_info("Resetting task handler");
    this->_task_handler->reset();
    cpp_utils::print_info("Resetting core");
    response["result"]=true;
    if(!this->_core->reset()){
        cpp_utils::print_error("Reset failed, could not reinitialize core.");
        response["error"]="Reset failed, could not reinitialize core.";
        response["result"]=false;
    }
    this->_task_handler->set_interrupt(false);
    return response;
}

nlohmann::json WSServer::unlock_brakes(const nlohmann::json &request){
    cpp_utils::print_info("Attempting to unlock brakes.");
    this->_core->unlock_brakes();
    return nlohmann::json();
}

nlohmann::json WSServer::lock_brakes(const nlohmann::json &request){
    cpp_utils::print_info("Attempting to lock brakes.");
    this->_core->lock_brakes();
    return nlohmann::json();
}

nlohmann::json WSServer::shutdown(const nlohmann::json &request){
    cpp_utils::print_info("Attempting to shutdown.");
    this->_core->shutdown_robot();
    return nlohmann::json();
}

nlohmann::json WSServer::pack_pose(const nlohmann::json &request){
    nlohmann::json response;
    cpp_utils::print_info("Attempting to move to pack pose.");
    response["error"]="";
    if(this->_core->is_grasping()){
        cpp_utils::print_error("The robot might be holding an object. Moving to pack pose is not safe.");
        response["error"]="The robot might be holding an object. Moving to pack pose is not safe.";
        response["result"]=false;
        return response;
    }
    response["result"]=this->_core->move_to_pack_pose();
    return response;
}

}
