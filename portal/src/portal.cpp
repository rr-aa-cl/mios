#include "portal/portal.hpp"

#include <msrm_utils/network.hpp>
#include "msrm_utils/system.hpp"
#include <spdlog/spdlog.h>

namespace mios {

Portal::Portal(const std::string &websocket_address, unsigned websocket_port, const std::string &websocket_endpoint, const std::string &rpc_address, unsigned rpc_port, unsigned udp_port):
m_keep_running(false){
    spdlog::info("Initializing portal...");
    m_servers.insert(std::make_pair(JsonServers::Websocket,std::make_unique<msrm_utils::JsonWebsocketServer>(websocket_address,websocket_port,websocket_endpoint)));
    m_servers.insert(std::make_pair(JsonServers::RPC,std::make_unique<msrm_utils::JsonRPCServer>(rpc_address,rpc_port)));
    m_servers.insert(std::make_pair(JsonServers::UDP,std::make_unique<msrm_utils::JsonUDPServer>(udp_port)));
    unsigned n_failures=0;
    for(const auto& s : m_servers){
        if(!s.second->start_listening()){
            n_failures++;
            if(s.first==JsonServers::Websocket){
                spdlog::warn("Could not start websocket server with parameters: [address: "+websocket_address+", port: "+std::to_string(websocket_port)+", endpoint: "+websocket_endpoint+"]");
            }
            if(s.first==JsonServers::Websocket){
                spdlog::warn("Could not start rpc server with parameters: [address: "+rpc_address+", port: "+std::to_string(rpc_port)+"]");
            }
            if(s.first==JsonServers::UDP){
                spdlog::warn("Could not start udp server with parameters: [port: "+std::to_string(udp_port)+"]");
            }
        }
    }
    if(n_failures>=m_servers.size()){
        spdlog::critical("Could not start any communication interfaces.");
    }
    m_keep_running=true;
    m_message_thread = std::thread(&Portal::send_messages,this);
}

Portal::~Portal(){
    for(const auto& s : m_servers){
        s.second->stop_listening();
    }
    m_keep_running=false;
    if(m_message_thread.joinable()){
        m_message_thread.join();
    }
}

void Portal::bind_method_to_websocket_server(const char *method_name, std::function<nlohmann::json (const nlohmann::json &)> method_callback,
                                             const std::vector<msrm_utils::ArgPair> &method_arguments){
    m_servers[JsonServers::Websocket]->bind_method(method_name,method_callback,method_arguments);
}

void Portal::bind_method_to_rpc_server(const char *method_name, std::function<nlohmann::json (const nlohmann::json &)> method_callback,const std::vector<msrm_utils::ArgPair> &method_arguments){
    m_servers[JsonServers::RPC]->bind_method(method_name,method_callback,method_arguments);
}

void Portal::bind_method_to_udp_server(const char *method_name, std::function<nlohmann::json (const nlohmann::json &)> method_callback,const std::vector<msrm_utils::ArgPair> &method_arguments){
    m_servers[JsonServers::UDP]->bind_method(method_name,method_callback,method_arguments);
}

void Portal::bind_method_to_all(const char *method_name, std::function<nlohmann::json (const nlohmann::json &)> method_callback,const std::vector<msrm_utils::ArgPair> &method_arguments){
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
    if(m_outstreams.find(name)!=m_outstreams.end()){
        spdlog::error("A UDP channel with name " + name + " already exists.");
        return nullptr;
    }
    m_outstreams.insert(std::make_pair(name,std::make_shared<msrm_utils::UDPStreamSender>(address,port)));
    return m_outstreams[name];
}

std::shared_ptr<msrm_utils::UDPStreamReceiver> Portal::open_udp_instream(const std::string &name, unsigned port, unsigned buffer_size,unsigned timeout_s,unsigned timeout_us,unsigned max_lost_packet,std::function<void(std::vector<double>&)> callback){
    if(m_instreams.find(name)!=m_instreams.end()){
        spdlog::error("A UDP channel with name " + name + " already exists.");
        return nullptr;
    }
    m_instreams.insert(std::make_pair(name,std::make_shared<msrm_utils::UDPStreamReceiver>(port,buffer_size,timeout_s,timeout_us,max_lost_packet,callback)));
    return m_instreams[name];
}

void Portal::close_udp_outstream(const std::string &name){
    if(m_outstreams.find(name)!=m_outstreams.end()){
        m_outstreams.erase(m_outstreams.find(name));
    }
}

void Portal::close_udp_instream(const std::string &name){
    if(m_instreams.find(name)!=m_instreams.end()){
        m_instreams.erase(m_instreams.find(name));
    }
}

std::string Portal::send_message(const std::string &address, unsigned int port, const std::string &method, const nlohmann::json request){
    std::scoped_lock<std::mutex> lock(m_mtx_message);
    m_message_queue.emplace(Message{address,port,method,request,msrm_utils::generate_uuid()});
    return m_message_queue.front().uuid;
}

nlohmann::json Portal::get_message_response(const std::string &message_uuid){
    std::scoped_lock<std::mutex> lock(m_mtx_message);
    if(m_message_responses.find(message_uuid)==m_message_responses.end()){
        return nlohmann::json();
    }else{
        nlohmann::json response = m_message_responses.at(message_uuid);
        m_message_responses.erase(m_message_responses.find(message_uuid));
        return response;
    }
}

void Portal::send_messages(){
    while(m_keep_running){
        m_mtx_message.lock();
        if(!m_message_queue.empty()){
            Message m = m_message_queue.front();
            m_mtx_message.unlock();
            nlohmann::json response;
            if(!msrm_utils::JsonWebsocketClient::call_method(m.address,m.port,"mios/core",m.method,m.request,response,5)){
                response=false;
            }
            m_mtx_message.lock();
            m_message_responses.emplace(std::make_pair(m.uuid,response));
            m_message_queue.pop();
        }
        m_mtx_message.unlock();
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

}
