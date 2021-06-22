#include "mios/data_structures/event.hpp"

namespace mios {

Event::Event(const std::string& name, const nlohmann::json& content):m_name(name),m_content(content){

}

void Event::update_content(const nlohmann::json &content){
    m_content=content;
}

nlohmann::json Event::get_content() const{
    return m_content;
}

std::string Event::get_name() const{
    return m_name;
}

}
