#include "interface/parameter_server.hpp"

#include "cpp_utils/json.hpp"
#include "cpp_utils/conversion.hpp"

namespace mios {

ParameterServer::ParameterServer(){
    this->_ws_server=nullptr;
}

ParameterServer::~ParameterServer(){

}

void ParameterServer::initialize(unsigned port){
    this->_ws_server = std::make_unique<cpp_utils::JsonWebsocketServer>("0.0.0.0",port,10,"mios/live");

    this->bind_methods();
}

void ParameterServer::start(){
    cpp_utils::print_info("Starting live parameter server at endpoint mios/live...",false);
    this->_ws_server->start_listening();
    cpp_utils::print_info("done.");
}

void ParameterServer::stop(){
    cpp_utils::print_info("Stopping live parameter server...",false);
    this->_ws_server->stop_listening();
    cpp_utils::print_info("done.");
}

void ParameterServer::bind_methods(){
    this->_ws_server->bind_method("set_parameter",std::bind(&ParameterServer::set_parameter,this,std::placeholders::_1),{"parameter_key","parameter_value"});
}

nlohmann::json ParameterServer::set_parameter(const nlohmann::json &request){
    std::string key;
    nlohmann::json response;
    nlohmann::json value=request["parameter_value"];
    request["parameter_key"].get_to(key);
    cpp_utils::print_debug("Setting parameter "+key+".");
    this->_mtx_parameters.lock();
    if(this->_parameters.find(key)==this->_parameters.end()){
        this->_parameters.insert(std::pair<std::string,nlohmann::json>(key,value));
    }else{
        this->_parameters[key]=value;
    }
    this->_mtx_parameters.unlock();
    response["result"]=true;
    return response;
}

nlohmann::json ParameterServer::get_parameter(const std::string &parameter){
    nlohmann::json rtn;
    this->_mtx_parameters.lock();
    if(this->_parameters.find(parameter)==this->_parameters.end()){
//        cpp_utils::print_warning("Parameter "+parameter+" not found in live parameter server, returning null.");
        rtn=nlohmann::json();
    }else{
        rtn=this->_parameters.at(parameter);
    }
    this->_mtx_parameters.unlock();
    return rtn;
}

}
