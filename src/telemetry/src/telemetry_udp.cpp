#include "telemetry/telemetry_udp.hpp"

#include "msrm_cpp_utils/network.hpp"
#include "msrm_cpp_utils/output.hpp"
#include "spdlog/spdlog.h"

#include "core/core.hpp"
#include "portal/portal.hpp"


namespace mios {

TelemetryUDP::TelemetryUDP(Core *core, Portal* portal):m_core(core),m_portal(portal),m_thread_running(false),m_keep_running(false),m_frequency(5){
    start_sending();
}

TelemetryUDP::~TelemetryUDP(){
    stop_sending();
}

bool TelemetryUDP::add_subscriber(const std::string &addr, const unsigned port, const std::vector<std::string> &subs,
                                  bool sendWithTerminatingNullCharacter){
    // check ip address:
    std::string ip = addr;
    if(!msrm_utils::is_valid_ip_address(addr.c_str())){
        ip = msrm_utils::get_ip_by_hostname(addr.c_str()).value_or("none");  //dns request for addr (hostname)
    }
    if(!msrm_utils::is_valid_ip_address(ip.c_str())){
        spdlog::error("Telemetry_UDP.add_subscriber: Invalid IP address " + addr + " set for telemetry.");
        return false;
    }
    // is subscriber already in subscriber list?
    m_mtx_subscriber.lock();
    auto it = std::find_if(m_subscribers.begin(), m_subscribers.end(),
                    [&ip_temp = addr](const Subscriber &sub) -> bool
                    { return ip_temp == sub.address; });
    if(it == m_subscribers.end()){
        std::string name = "telemetry_" + ip + ":" + std::to_string(port);
        Subscriber sub_temp = {port, ip, addr, subs, sendWithTerminatingNullCharacter,
                               m_portal->open_udp_outstream(name, ip, port)};
        m_subscribers.push_back(sub_temp);  // add new subscriber
        if(!sub_temp.stream->connect()){
            spdlog::error("Could not connect outgoing UDP stream to " + sub_temp.address + ":" + std::to_string(sub_temp.port));
        }else{
            spdlog::debug("TelemetryUDP::add_subscriber: Subscriber " + sub_temp.address + ":"+std::to_string(sub_temp.port) + " added.");
        }
    }
    else{  // update subscriber
        spdlog::debug("TelemetryUDP::add_subscriber: Updating existing Subsciber " + (*it).address + ":"+std::to_string((*it).port));
        (*it).subscriptions = subs;
    }
    m_mtx_subscriber.unlock();
    return true;
}

bool TelemetryUDP::remove_subscriber(const std::string &addr){
    unsigned retry_cnt = 0;
    while(true){
        if(m_mtx_subscriber.try_lock()){
            auto it = std::find_if(m_subscribers.begin(), m_subscribers.end(),
                            [&ip_temp = addr](const Subscriber &sub) -> bool
                            { return ip_temp == sub.address; });
            if(it == m_subscribers.end()) {
                // no subscriber with this addr found
                spdlog::debug("TelemetryUDP::remove_subscriber: No subscriber with address "+addr+" found.");
                m_mtx_subscriber.unlock();
                return false;
            }
            spdlog::debug("TelemetryUDP::remove_subscriber: removing subscriber... "+(*it).ip +":"+ std::to_string((*it).port));
            std::string name = "telemetry_" + (*it).ip + ":" + std::to_string((*it).port);
            m_portal->close_udp_outstream(name);
            m_subscribers.erase(it);
            m_mtx_subscriber.unlock();
            spdlog::debug("TelemetryUDP::remove_subscriber: removed subscriber "+addr);
            return true;

        }
        if(retry_cnt > 10){
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
    }
    return false;
}
bool TelemetryUDP::start_sending(){
    spdlog::trace("TelemetryUDP::start_sending()");
    // start sending_loop in own thread
    if(m_keep_running){
        return true;
    }
    m_keep_running = true;
    m_thr_send = std::thread(&TelemetryUDP::sending_loop, this);
    m_thread_running = true;
    spdlog::info("Telemetry has been started.");
    return true;

}

bool TelemetryUDP::stop_sending(){
    spdlog::trace("TelemetryUDP::stop_sending()");
    // keep running false, join running thread
    m_keep_running = false;
    if(m_thread_running){
        m_thr_send.join();
        m_thread_running = false;
    }
    spdlog::info("Telemetry has been terminated.");
    return true;
}

void TelemetryUDP::sending_loop(){
    spdlog::trace("TelemetryUDP::sending_loop()");
    while(m_keep_running){
        m_time_1 = std::chrono::high_resolution_clock::now();
        // get current perception
        if(!m_core->is_busy()){
            if(!m_core->refresh_percept({})){
                spdlog::warn("No current state available, could not refresh perception.");
            }
        }
        const Percept* p = m_core->get_percept();
        m_mtx_subscriber.lock();
        for(auto sub : m_subscribers){
            // build message for every subscriber
            nlohmann::json msg_data;
            for(std::string subscription : sub.subscriptions){
                switch(m_data_map.find(subscription)->second){
                case 1: msrm_utils::write_json_array<double,4,4>(msg_data["O_T_EE"],p->proprioception.O_T_EE); break;
                case 2: msrm_utils::write_json_array<double,4,4>(msg_data["T_T_EE"],p->proprioception.T_T_EE); break;
                case 3: msrm_utils::write_json_array<double,7,1>(msg_data["q"],p->proprioception.q); break;
                case 4: msrm_utils::write_json_array<double,7,1>(msg_data["dq"],p->proprioception.dq); break;
                case 5: msrm_utils::write_json_array<double,7,1>(msg_data["theta"],p->proprioception.theta); break;
                case 6: msrm_utils::write_json_array<double,7,1>(msg_data["dtheta"],p->proprioception.dtheta); break;
                case 7: msrm_utils::write_json_array<double,6,1>(msg_data["O_dX_EE"],p->proprioception.O_dX_EE); break;
                case 8: msrm_utils::write_json_array<double,6,1>(msg_data["EE_dX_EE"],p->proprioception.EE_dX_EE); break;
                case 9: msrm_utils::write_json_array<double,6,1>(msg_data["F_dX_EE"],p->proprioception.TF_dX_EE); break;
                case 10: msrm_utils::write_json_array<double,7,1>(msg_data["tau_ext"],p->proprioception.tau_ext); break;
                case 11: msrm_utils::write_json_array<double,7,1>(msg_data["tau_j"],p->proprioception.tau_j); break;
                case 12: msrm_utils::write_json_array<double,6,1>(msg_data["K_F_ext_K"],p->proprioception.K_F_ext_K); break;
                case 13: msrm_utils::write_json_array<double,6,1>(msg_data["K_dF_ext_K"],p->proprioception.K_dF_ext_K); break;
                case 14: msrm_utils::write_json_array<double,6,1>(msg_data["O_F_ext_K"],p->proprioception.O_F_ext_K); break;
                case 15: msrm_utils::write_json_array<double,6,1>(msg_data["O_dF_ext_K"],p->proprioception.O_dF_ext_K); break;
                case 16: msrm_utils::write_json_array<double,6,1>(msg_data["TF_F_ext_K"],p->proprioception.TF_F_ext_K); break;
                case 17: msrm_utils::write_json_array<double,6,1>(msg_data["TF_dF_ext_K"],p->proprioception.TF_dF_ext_K); break;
                case 18: msg_data["finger_width"] = p->proprioception.finger_width; break;
                case 19: msg_data["finger_temperature"] = p->proprioception.finger_temperature; break;
                case 20: msg_data["is_grasping"] = p->proprioception.is_grasping; break;
                case 21: msrm_utils::write_json_array<double,7,7>(msg_data["M"],p->internal_model.M); break;
                case 22: msrm_utils::write_json_array<double,7,1>(msg_data["C"],p->internal_model.C); break;
                case 23: msrm_utils::write_json_array<double,7,1>(msg_data["G"],p->internal_model.G); break;
                case 24: msrm_utils::write_json_array<double,6,7>(msg_data["B_J_EE"],p->internal_model.B_J_EE); break;
                case 25: msrm_utils::write_json_array<double,6,7>(msg_data["B_J_O"],p->internal_model.B_J_O); break;
                case 26: msg_data["max_finger_width"] = p->internal_model.max_finger_width; break;
                case 27: {
                    HandActivityState handactivity = p->internal_model.hand_activity_state;
                    if(handactivity == HandActivityState::hsIdle){
                        msg_data["hand_activity_state"] = "hsIdle";
                    }else if(handactivity == HandActivityState::hsBusy){
                        msg_data["hand_activity_state"] = "hsBusy";
                    }else if(handactivity == HandActivityState::hsFinished){
                        msg_data["hand_activity_state"] = "hsFinished";
                    }else {
                        msg_data["hand_activity_state"] = "ERROR: no defined HandActivityState";
                    }
                    break;
                }
                case 28: msrm_utils::write_json_array<double,6,1>(msg_data["e"],p->controller.e); break;
                case 29: msrm_utils::write_json_array<double,6,1>(msg_data["rho"],p->controller.rho); break;
                case 30: msrm_utils::write_json_array<double,6,1>(msg_data["K_x"],p->controller.K_x); break;
                case 31: msrm_utils::write_json_array<double,6,1>(msg_data["xi_x"],p->controller.xi_x); break;
                case 32: msrm_utils::write_json_array<double,7,1>(msg_data["K_theta"],p->controller.K_theta); break;
                case 33: msrm_utils::write_json_array<double,7,1>(msg_data["xi_theta"],p->controller.xi_theta); break;
                case 34: msrm_utils::write_json_array<double,4,4>(msg_data["TF_T_EE_d"],p->controller.TF_T_EE_d); break;
                case 35: msrm_utils::write_json_array<double,6,1>(msg_data["TF_dX_d"],p->controller.TF_dX_d); break;
                case 36: msrm_utils::write_json_array<double,6,1>(msg_data["TF_F_ff"],p->controller.TF_F_ff); break;
                case 37: msrm_utils::write_json_array<double,3,3>(msg_data["O_R_T"],p->controller.O_R_T); break;
                case 38: msrm_utils::write_json_array<double,7,1>(msg_data["q_d"],p->controller.q_d); break;
                case 39: msrm_utils::write_json_array<double,7,1>(msg_data["dq_d"],p->controller.dq_d); break;
                case 40: msrm_utils::write_json_array<double,7,1>(msg_data["tau_ff"],p->controller.tau_ff); break;
                default: msg_data[subscription] = "Not a defined Telemetry.";
                }
            }
            // send to every subscriber
            sub.stream->send(msg_data.dump(), sub.sendWithTerminatingNullCharacter);
        }
        m_mtx_subscriber.unlock();
        m_time_2 = std::chrono::high_resolution_clock::now();
        m_time_duration = m_time_2 - m_time_1;
        // wait
        std::this_thread::sleep_for(std::chrono::milliseconds(m_frequency) - m_time_duration);
    }
}

}
