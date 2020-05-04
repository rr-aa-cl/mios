#pragma once

#include <vector>
#include <set>
#include <nlohmann/json.hpp>

namespace mios {

class EventPublisher{
public:
    EventPublisher(const EventPublisher&) = delete;

    static EventPublisher& get();

    static void publish_event(const nlohmann::json& event);
    static void subscribe(const std::pair<std::string, unsigned> &subscriber);
    static void unsubscribe(const std::pair<std::string, unsigned> &subscriber);
private:
    void i_publish_event(const nlohmann::json& event);
    void i_subscribe(const std::pair<std::string,unsigned>&  subscriber);
    void i_unsubscribe(const std::pair<std::string, unsigned> &subscriber);
    EventPublisher(){}

    nlohmann::json events;
    std::set<std::pair<std::string,unsigned> > m_subscribers;
};

}
