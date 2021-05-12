#include "telemetry/telemetry_udp.hpp"

#include <msrm_utils/network.hpp>
#include <msrm_utils/output.hpp>


#include <spdlog/spdlog.h>
#include "core/core.hpp"


namespace mios {
class Core;

Telemetry_UDP::Telemetry_UDP(Core *core):m_core(core),keep_running(false),m_frequency(200){

}

Telemetry_UDP::~Telemetry_UDP(){
    keep_running = false;
    thread_running = false;
}

bool Telemetry_UDP::send(const nlohmann::json &msg_data, const std::string &address, const unsigned port){
    struct sockaddr_in m_si_other;
    unsigned m_slen = sizeof(m_si_other);
    if ((m_socket=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) // If socket for outgoing connection could not be created...
    {
        spdlog::error("Telemetry_UDP.send: Could not create socket: ");
        std::cout << std::strerror(errno) << std::endl;
        return false;
    }

    memset((char *) &m_si_other, 0, m_slen);                    // clear address
    m_si_other.sin_family = AF_INET;                            // set socket family
    m_si_other.sin_port = htons(port);                          // set port

    if(inet_aton(address.c_str(), &m_si_other.sin_addr)==0){    // make ip address binary
        spdlog::error("Telemetry_UDP.send: Invalid address: "+address+", port: "+std::to_string(port));
        return false;
    }

    std::string payload = msg_data.dump();
    const char* msg = payload.c_str();
    int result = sendto(m_socket, msg, strlen(msg), 0, (struct sockaddr *) &m_si_other, m_slen);  //flag MSG_CONFIRM
    if(result<0){
        spdlog::error("Telemetry_UDP.send: Could not send message: ");
        std::cout<<std::strerror(errno)<<std::endl;
        return false;
    }
    close(m_socket);
    return true;
}

bool Telemetry_UDP::add_subscriber(const std::string &addr, const unsigned port, const std::vector<std::string> &subs){
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
    Subscriber sub_temp = {port, ip, addr, subs};
    auto it = std::find_if(subscriber_vector.begin(), subscriber_vector.end(), 
             [&ip_temp = addr]
             (const Subscriber &sub) -> bool { return ip_temp == sub.address; }); 
    if(it == subscriber_vector.end()){
        subscriber_vector.push_back(sub_temp);  // add new subscriber
        spdlog::debug("Telemetry_UDP.add_subscriber: Subscriber " + sub_temp.address + ":"+std::to_string(sub_temp.port));
    }
    else{  // update subscriber
        spdlog::debug("Telemetry_UDP.add_subscriber: update existing Subsciber " + sub_temp.address + ":"+std::to_string(sub_temp.port));
        for(auto &sub : subscriber_vector){
            if(sub.address == sub_temp.address){
                sub.subscribtions = sub_temp.subscribtions;
                sub.port = sub_temp.port;
            }
        }
    }
    return Telemetry_UDP::start_sending();
}
bool Telemetry_UDP::start_sending(){
    // start sending_loop in own thread
    if(keep_running){
        return true;
    }
    keep_running = true;
    spdlog::debug("Telemetry_UDP.start_sending "+std::to_string(keep_running));
    sending_thread = std::thread(&Telemetry_UDP::sending_loop, this);
    thread_running = true;
    return true;

}
bool Telemetry_UDP::stop_sending(){
    // keep running false, join running thread
    spdlog::debug("Telemetry_UDP.stop_sending: terminating sending thread...");
    keep_running = false;
    if(thread_running){
        sending_thread.join();
        thread_running = false;
    }
    spdlog::debug("Telemetry_UDP.stop_sending: sending thread terminated ");
    return true;
}
void Telemetry_UDP::sending_loop(){
    spdlog::debug("Telemetry_UDP.sending_loop started");
    while(keep_running){
        time_1 = std::chrono::high_resolution_clock::now();
        // get current percept
        if(!m_core->refresh_percept({})){
            spdlog::error("No current state available, could not refresh perception.");
        }
        const Percept* p = m_core->get_percept();
        for(auto sub : subscriber_vector){
            // build message for every subscriber
            nlohmann::json msg_data;
            for(std::string subscribtion : sub.subscribtions){
                switch(perception.find(subscribtion)->second){
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
                    default: msg_data["Error"] = "No definded Telemetry subscribed";
                }
            }
            // send to every subscriber
            bool works = send(msg_data, sub.ip, sub.port);
        }
        time_2 = std::chrono::high_resolution_clock::now();
        time_duration = time_2 - time_1;
        // wait
        std::this_thread::sleep_for(std::chrono::milliseconds(m_frequency) - time_duration);
    }
}


}
