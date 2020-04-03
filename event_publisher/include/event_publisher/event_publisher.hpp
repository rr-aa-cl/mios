#pragma once

#include <vector>
#include <set>

namespace mios {

class EventPublisher{
public:
    EventPublisher(const EventPublisher&) = delete;

    static EventPublisher& get();

    static void publish_event(const char* event);
    static void subscribe(const char* subscriber);
private:
    void i_publish_event(const char* event);
    void i_subscribe(const char* subscriber);
    EventPublisher(){}

    std::set<const char*> m_subscribers;
};

}
