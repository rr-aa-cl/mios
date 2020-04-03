#include "event_publisher/event_publisher.hpp"

#include "cpp_utils/network.hpp"

namespace mios
{

EventPublisher& EventPublisher::get(){
    static EventPublisher instance;
    return instance;
}

void EventPublisher::publish_event(const char *event){
    get().i_publish_event(event);
}

void EventPublisher::subscribe(const char *subscriber){
    get().subscribe(subscriber);
}

void EventPublisher::i_publish_event(const char *event){
    for(const char* addr : m_subscribers){
        nlohmann::json response;
        cpp_utils::rpc_call(addr,10000,"event",{event},response);
    }
}

void EventPublisher::i_subscribe(const char *subscriber){
    m_subscribers.insert(subscriber);
}

}
