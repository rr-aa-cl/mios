#include "portal/portal.hpp"

#include <msrm_utils/network.hpp>
#include <spdlog/spdlog.h>

namespace mios {

Portal::Portal(const std::string &websocket_address, unsigned websocket_port, const std::string &websocket_endpoint, const std::string &rpc_address, unsigned rpc_port, unsigned udp_port){
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
}

Portal::~Portal(){
    for(const auto& s : m_servers){
        s.second->stop_listening();
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

}
