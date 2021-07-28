#include "mios/portal/portal.hpp"

#include "msrm_cpp_utils/system/system.hpp"

#include "spdlog/spdlog.h"

namespace mios {

Portal::Portal(const std::string &websocket_address, unsigned websocket_port, const std::string &websocket_endpoint, const std::string &rpc_address, unsigned rpc_port, unsigned udp_port):
    m_keep_running(false),m_websocket_address(websocket_address),m_websocket_port(websocket_port),m_websocket_endpoint(websocket_endpoint),m_rpc_address(rpc_address),m_rpc_port(rpc_port),
    m_udp_port(udp_port){
    spdlog::trace("Portal::Portal");
    m_servers.insert(std::make_pair(JsonServers::Websocket,std::make_unique<msrm_utils::JsonWebsocketServer>("mios-interface",m_websocket_address,m_websocket_port,m_websocket_endpoint)));
    //    m_servers.insert(std::make_pair(JsonServers::RPC,std::make_unique<msrm_utils::JsonRPCServer>(m_rpc_address,m_rpc_port)));
    m_servers.insert(std::make_pair(JsonServers::UDP,std::make_unique<msrm_utils::JsonUDPServer>("mios-interface",m_udp_port)));
}

Portal::~Portal(){
    spdlog::trace("Portal::~Portal");
    for(const auto& s : m_servers){
        s.second->stop_listening();
    }
    m_keep_running=false;
    if(m_message_thread.joinable()){
        m_message_thread.join();
    }
}

bool Portal::initialize(){
    spdlog::trace("Portal::initialize");
    unsigned n_failures=0;
    for(const auto& s : m_servers){
        if(!s.second->start_listening()){
            n_failures++;
            if(s.first==JsonServers::Websocket){
                spdlog::warn("Could not start websocket server with parameters: [address: "+m_websocket_address+", port: "+std::to_string(m_websocket_port)+", endpoint: "+m_websocket_endpoint+"]");
            }
            if(s.first==JsonServers::RPC){
                spdlog::warn("Could not start rpc server with parameters: [address: "+m_rpc_address+", port: "+std::to_string(m_rpc_port)+"]");
            }
            if(s.first==JsonServers::UDP){
                spdlog::warn("Could not start udp server with parameters: [port: "+std::to_string(m_udp_port)+"]");
            }
        }
    }
    if(n_failures>=m_servers.size()){
        spdlog::error("Could not start any communication interfaces.");
        return false;
    }
    m_keep_running=true;
    m_message_thread = std::thread(&Portal::send_messages,this);
    return true;
}

void Portal::bind_method_to_websocket_server(const char *method_name, std::function<nlohmann::json (const nlohmann::json &)> method_callback,
                                             const std::vector<msrm_utils::ArgPair> &method_arguments){
    spdlog::trace("Portal::bind_method_to_websocket_server");
    m_servers[JsonServers::Websocket]->bind_method(method_name,method_callback,method_arguments);
}

void Portal::bind_method_to_rpc_server(const char *method_name, std::function<nlohmann::json (const nlohmann::json &)> method_callback,const std::vector<msrm_utils::ArgPair> &method_arguments){
    spdlog::trace("Portal::bind_method_to_rpc_server");
    m_servers[JsonServers::RPC]->bind_method(method_name,method_callback,method_arguments);
}

void Portal::bind_method_to_udp_server(const char *method_name, std::function<nlohmann::json (const nlohmann::json &)> method_callback,const std::vector<msrm_utils::ArgPair> &method_arguments){
    spdlog::trace("Portal::bind_method_to_udp_server");
    m_servers[JsonServers::UDP]->bind_method(method_name,method_callback,method_arguments);
}

void Portal::bind_method_to_all(const char *method_name, std::function<nlohmann::json (const nlohmann::json &)> method_callback,const std::vector<msrm_utils::ArgPair> &method_arguments){
    spdlog::trace("Portal::bind_method_to_all");
    for(const auto& s : m_servers){
        if(!s.second->bind_method(method_name,method_callback,method_arguments)){
            if(s.first==JsonServers::Websocket){
                spdlog::warn("Could not bind method with name "+std::string(method_name)+" to websocket server.");
            }
            if(s.first==JsonServers::Websocket){
                spdlog::warn("Could not bind method with name "+std::string(method_name)+" to rpc server.");
            }
            if(s.first==JsonServers::UDP){
                spdlog::warn("Could not bind method with name "+std::string(method_name)+" to udp server.");
            }
        }
    }
}

std::shared_ptr<msrm_utils::UDPStreamSender> Portal::open_udp_outstream(const std::string &name, const std::string &address, unsigned int port){
    spdlog::trace("Portal::open_udp_outstream");
    if(m_outstreams.find(name)!=m_outstreams.end()){
        spdlog::error("A UDP channel with name " + name + " already exists.");
        return nullptr;
    }
    m_outstreams.insert(std::make_pair(name,std::make_shared<msrm_utils::UDPStreamSender>(name,address,port)));
    return m_outstreams[name];
}

std::shared_ptr<msrm_utils::UDPStreamReceiver> Portal::open_udp_instream(const std::string &name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us, unsigned max_lost_packet, std::function<void(std::vector<double>&)> callback, bool multicast){
    spdlog::trace("Portal::open_udp_instream");
    if(m_instreams.find(name)!=m_instreams.end()){
        spdlog::error("A UDP channel with name " + name + " already exists.");
        return nullptr;
    }
    m_instreams.insert(std::make_pair(name,std::make_shared<msrm_utils::UDPStreamReceiver>(name,port,buffer_size,timeout_s,timeout_us,max_lost_packet,callback,multicast)));
    return m_instreams[name];
}

void Portal::close_udp_outstream(const std::string &name){
    spdlog::trace("Portal::close_udp_outstream");
    if(m_outstreams.find(name)!=m_outstreams.end()){
        m_outstreams.erase(m_outstreams.find(name));
    }
}

void Portal::close_udp_instream(const std::string &name){
    spdlog::trace("Portal::close_udp_instream");
    if(m_instreams.find(name)!=m_instreams.end()){
        m_instreams.erase(m_instreams.find(name));
    }
}

std::string Portal::send_message(const std::string &address, unsigned int port, const std::string &method, const nlohmann::json request, std::string protocol, double timeout, bool repeat){
    spdlog::trace("Portal::send_message");
    std::scoped_lock<std::mutex> lock(m_mtx_message);
    std::string msg_uuid = msrm_utils::generate_uuid();
    m_message_queue.insert(std::pair<std::string,Message>(msg_uuid,Message{address,port,method,request,msg_uuid,protocol,timeout,repeat}));
    return msg_uuid;
}

nlohmann::json Portal::get_message_response(const std::string &message_uuid){
    spdlog::trace("Portal::get_message_response");
    std::scoped_lock<std::mutex> lock(m_mtx_message);
    if(m_message_responses.find(message_uuid)==m_message_responses.end()){
        return nlohmann::json();
    }else{
        nlohmann::json response = m_message_responses.at(message_uuid);
        m_message_responses.erase(m_message_responses.find(message_uuid));
        return response;
    }
}

void Portal::remove_message(const std::string& message_uuid){
    std::scoped_lock<std::mutex> lock(m_mtx_message);
    m_message_queue.erase(message_uuid);
}

void Portal::remove_messages(){
    m_mtx_message.lock();
    m_message_queue.clear();
    m_mtx_message.unlock();
}

void Portal::send_messages(){
    spdlog::trace("Portal::send_messages");
    while(m_keep_running){
        bool result=true;
        std::set<std::string> finished_messages;
        m_mtx_message.lock();
        std::unordered_map<std::string,Message> message_pool_copy=m_message_queue;
        m_mtx_message.unlock();
        for(auto m : message_pool_copy){
            nlohmann::json response;
            spdlog::debug("Sending message to " + m.second.address + ":" + std::to_string(m.second.port));
            result=true;
            if(m.second.protocol=="websocket"){
                if(!msrm_utils::JsonWebsocketClient::call_method(m.second.address,m.second.port,"mios/core",m.second.method,m.second.request,response,m.second.timeout)){
                    result=false;
                    response=false;
                }
            }
            else if(m.second.protocol=="udp"){
                if(!msrm_utils::JsonUDPClient::call_method(m.second.address,m.second.port,m.second.method,m.second.request,response,static_cast<int>(m.second.timeout))){
                    result=false;
                    response=false;
                }
            }else{
                spdlog::error("Cannot send message via protocol " + m.second.protocol);
                response=false;
                break;
            }
            if(result){
                finished_messages.insert(m.first);
            }
            m_mtx_message.lock();
            m_message_responses.emplace(std::make_pair(m.first,response));
            m_mtx_message.unlock();
        }
        m_mtx_message.lock();
        for(auto uuid : finished_messages){
            m_message_queue.erase(uuid);
        }
        m_mtx_message.unlock();
        //        if(!m_message_queue.empty()){
        //            Message m = m_message_queue.front();
        //            m_mtx_message.unlock();
        //            nlohmann::json response;
        //            bool result=true;
        //            do{
        //                spdlog::debug("Sending message to " + m.address + ":" + std::to_string(m.port));
        //                result=true;
        //                if(m.protocol=="websocket"){
        //                    if(!msrm_utils::JsonWebsocketClient::call_method(m.address,m.port,"mios/core",m.method,m.request,response,m.timeout)){
        //                        result=false;
        //                        response=false;
        //                    }
        //                }
        //                else if(m.protocol=="udp"){
        //                    if(!msrm_utils::JsonUDPClient::call_method(m.address,m.port,m.method,m.request,response,static_cast<int>(m.timeout))){
        //                        result=false;
        //                        response=false;
        //                    }
        //                }else{
        //                    spdlog::error("Cannot send message via protocol " + m.protocol);
        //                    response=false;
        //                    break;
        //                }
        //            }while(m.repeat && !result);
        //            m_mtx_message.lock();
        //            m_message_responses.emplace(std::make_pair(m.uuid,response));
        //            m_message_queue.pop();
        //        }
        //        m_mtx_message.unlock();
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

}
