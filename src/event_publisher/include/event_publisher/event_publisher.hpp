#pragma once

#include <vector>
#include <set>
#include <nlohmann/json.hpp>
#include <mutex>
#include <thread>

namespace mios {

struct EventSubscriber{
    std::string uuid;
    std::string address;
    unsigned port;
    std::string endpoint;
    std::string method_name;

    bool operator<(const EventSubscriber& rhs) const
    {
      return uuid < rhs.uuid;
    }

    bool operator==(const EventSubscriber& rhs) const
    {
      return uuid == rhs.uuid;
    }
};

class EventPublisher{
public:
    EventPublisher(const EventPublisher&) = delete;

    static EventPublisher& get();

    static void publish_event(const nlohmann::json& event);
    static std::string subscribe(const EventSubscriber &subscriber);
    static void unsubscribe(const std::string& subscriber_uuid);
    static bool is_sending();
private:
    bool i_is_sending();
    void i_publish_event(const nlohmann::json& event);
    std::string i_subscribe(const EventSubscriber& subscriber);
    void i_unsubscribe(const std::string& subscriber_uuid);

    void publish(nlohmann::json event);
    EventPublisher(){}

    nlohmann::json events;
    std::set<EventSubscriber> m_subscribers;
    std::map<std::string,unsigned> m_failed_calls;
    std::mutex m_mtx_call;
    std::thread m_publish_thread;
    std::atomic<bool> m_active_call;

};

}
