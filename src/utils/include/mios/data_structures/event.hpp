#pragma once

#include <string>
#include <chrono>
#include "nlohmann/json.hpp"

namespace mios {

class Event{
public:
    Event(const std::string& name, const nlohmann::json& content);
    void update_content(const nlohmann::json& content);
    nlohmann::json get_content() const;
    std::string get_name() const;

private:
    const std::string m_name;
    nlohmann::json m_content;
    const std::chrono::high_resolution_clock::time_point m_timestamp;
};

}
