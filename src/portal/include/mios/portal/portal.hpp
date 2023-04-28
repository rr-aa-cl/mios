#pragma once


#include "nlohmann/json.hpp"
#include "mirmi_cpp_utils/network/network.hpp"

#include <string>
#include <vector>
#include <functional>
#include <vector>
#include <map>
#include <unordered_map>
#include <queue>
#include <thread>
#include <mutex>
#include <memory>

namespace mios {

enum JsonServers{Websocket,RPC,UDP};

struct Message{
    std::string address;
    unsigned port;
    std::string method;
    nlohmann::json request;
    std::string uuid;
    std::string protocol;
    double timeout;
    bool repeat;
};

class Portal{
public:
    Portal(const std::string& websocket_address, unsigned websocket_port, const std::string& websocket_endpoint,
           const std::string& rpc_address, unsigned rpc_port, unsigned udp_port);
    Portal(const Portal&) = delete;
    ~Portal();

    bool initialize();

    void bind_method_to_websocket_server(const char* method_name, std::function<nlohmann::json(const nlohmann::json&)> method_callback, const std::vector<mirmi_utils::ArgPair> &method_arguments);
    void bind_method_to_rpc_server(const char* method_name, std::function<nlohmann::json(const nlohmann::json&)> method_callback, const std::vector<mirmi_utils::ArgPair> &method_arguments);
    void bind_method_to_udp_server(const char* method_name, std::function<nlohmann::json(const nlohmann::json&)> method_callback, const std::vector<mirmi_utils::ArgPair> &method_arguments);
    void bind_method_to_all(const char* method_name, std::function<nlohmann::json(const nlohmann::json&)> method_callback, const std::vector<mirmi_utils::ArgPair> &method_arguments);

    std::shared_ptr<mirmi_utils::UDPStreamSender> open_udp_outstream(const std::string& name, const std::string &address, unsigned port, const std::optional<std::string>& host);
    std::shared_ptr<mirmi_utils::UDPStreamReceiver> open_udp_instream(const std::string &name, unsigned port, unsigned buffer_size,unsigned timeout_s,unsigned timeout_us,unsigned max_lost_packet,std::function<void(std::vector<double>&)> callback, bool multicast, const std::optional<std::string>& host, const std::optional<std::string> &multicast_group);
    void close_udp_outstream(const std::string& name);
    void close_udp_instream(const std::string& name);

    std::string send_message(const std::string& address, unsigned port, const std::string& method, const nlohmann::json request, std::string protocol="websocket", double timeout=5, bool repeat=false);
    nlohmann::json get_message_response(const std::string& message_uuid);
    void remove_message(const std::string& message_uuid);
    void remove_messages();

private:
    void send_messages();

private:
    bool m_keep_running;
    std::thread m_message_thread;
    std::mutex m_mtx_message;
    std::unordered_map<std::string,Message> m_message_queue;
    std::unordered_map<std::string,nlohmann::json> m_message_responses;

    std::unordered_map<std::string, std::shared_ptr<mirmi_utils::UDPStreamSender> > m_outstreams;
    std::unordered_map<std::string, std::shared_ptr<mirmi_utils::UDPStreamReceiver> > m_instreams;

    std::map<JsonServers,std::unique_ptr<mirmi_utils::IJsonMethodServer> > m_servers;

private:
    const std::string m_websocket_address;
    const unsigned m_websocket_port;
    const std::string m_websocket_endpoint;
    const std::string m_rpc_address;
    const unsigned m_rpc_port;
    const unsigned m_udp_port;
};

}
