#include "event_publisher/event_publisher.hpp"

#include <msrm_utils/network.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <sstream>
#include <spdlog/spdlog.h>

namespace mios
{

EventPublisher& EventPublisher::get(){
    static EventPublisher instance;
    return instance;
}

void EventPublisher::publish_event(const nlohmann::json& event){
    get().i_publish_event(event);
}

std::string EventPublisher::subscribe(const EventSubscriber& subscriber){
    return get().i_subscribe(subscriber);
}

void EventPublisher::unsubscribe(const std::string& subscriber_uuid){
    get().i_unsubscribe(subscriber_uuid);
}

bool EventPublisher::is_sending(){
    return get().i_is_sending();
}

void EventPublisher::i_publish_event(const nlohmann::json &event){
    if(m_active_call){
        return;
    }else if(m_publish_thread.joinable()){
        m_publish_thread.join();
    }
    m_publish_thread = std::thread(&EventPublisher::publish,this,event);
}

void EventPublisher::publish(nlohmann::json event){
    m_active_call=true;
    std::set<std::string> fail_queue;
    for(const EventSubscriber& subscriber : m_subscribers){
        nlohmann::json response;
        nlohmann::json request;
        request["event"]=event;
        if(!msrm_utils::JsonWebsocketClient::call_method(subscriber.address,subscriber.port,subscriber.endpoint,subscriber.method_name,request,response,2)){
            m_failed_calls[subscriber.uuid]++;
        }
        if(m_failed_calls[subscriber.uuid]>5){
            fail_queue.insert(subscriber.uuid);
        }
    }
    for(const std::string& uuid : fail_queue){
        i_unsubscribe(uuid);
    }
    m_active_call=false;
}

std::string EventPublisher::i_subscribe(const EventSubscriber& subscriber){
    if(subscriber.address=="none"){
        return "INVALID";
    }
    if(m_subscribers.find(subscriber)!=m_subscribers.end()){
        m_subscribers.erase(m_subscribers.find(subscriber));
    }
    m_subscribers.insert(subscriber);
    spdlog::debug("Someone subscribed: " + subscriber.address + ":" + std::to_string(subscriber.port) + "/" + subscriber.endpoint + "->" + subscriber.method_name);
    boost::uuids::uuid task_uuid = boost::uuids::random_generator()();
    std::stringstream ss;
    ss<<task_uuid;
    std::string uuid = ss.str();
    m_failed_calls.insert(std::make_pair(uuid,0));
    return uuid;
}

void EventPublisher::i_unsubscribe(const std::string &subscriber_uuid){
    spdlog::debug("Someone unsubscribed: " + subscriber_uuid);
    EventSubscriber tmp_sub;
    tmp_sub.uuid=subscriber_uuid;
    if(m_subscribers.find(tmp_sub)!=m_subscribers.end()){
        m_subscribers.erase(m_subscribers.find(tmp_sub));
        m_failed_calls.erase(m_failed_calls.find(subscriber_uuid));
    }
}

bool EventPublisher::i_is_sending(){
    bool is_locked = m_mtx_call.try_lock();
    if(is_locked){
        m_mtx_call.unlock();
    }
    return is_locked;
}

}
