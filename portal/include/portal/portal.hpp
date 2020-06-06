#pragma once

#include <functional>
#include <vector>
#include <map>
#include <nlohmann/json.hpp>
#include <msrm_utils/network.hpp>

namespace mios {

enum JsonServers{Websocket,RPC,UDP};

class Portal{
public:
    Portal(const std::string& websocket_address, unsigned websocket_port, const std::string& websocket_endpoint,
           const std::string& rpc_address, unsigned rpc_port, unsigned udp_port);
    Portal(const Portal&) = delete;
    ~Portal();

    void bind_method_to_websocket_server(const char* method_name, std::function<nlohmann::json(const nlohmann::json&)> method_callback, const std::vector<msrm_utils::ArgPair> &method_arguments);
    void bind_method_to_rpc_server(const char* method_name, std::function<nlohmann::json(const nlohmann::json&)> method_callback, const std::vector<msrm_utils::ArgPair> &method_arguments);
    void bind_method_to_udp_server(const char* method_name, std::function<nlohmann::json(const nlohmann::json&)> method_callback, const std::vector<msrm_utils::ArgPair> &method_arguments);
    void bind_method_to_all(const char* method_name, std::function<nlohmann::json(const nlohmann::json&)> method_callback, const std::vector<msrm_utils::ArgPair> &method_arguments);

    std::shared_ptr<msrm_utils::UDPStreamSender> open_udp_outstream(const std::string& name, const std::string &address, unsigned port);
    std::shared_ptr<msrm_utils::UDPStreamReceiver> open_udp_instream(const std::string &name, unsigned port, unsigned buffer_size,unsigned timeout_s,unsigned timeout_us,unsigned max_lost_packet,std::function<void(std::vector<double>&)> callback);
    void close_udp_outstream(const std::string& name);
    void close_udp_instream(const std::string& name);


private:
    std::unordered_map<std::string, std::shared_ptr<msrm_utils::UDPStreamSender> > m_outstreams;
    std::unordered_map<std::string, std::shared_ptr<msrm_utils::UDPStreamReceiver> > m_instreams;

    std::map<JsonServers,std::unique_ptr<msrm_utils::IJsonMethodServer> > m_servers;
};

}
