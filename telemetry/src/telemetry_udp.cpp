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

}

bool Telemetry_UDP::send(const nlohmann::json &msg_data, const std::string &address, const unsigned port){
    struct sockaddr_in m_si_other;
    unsigned m_slen = sizeof(m_si_other);
    if ((m_socket=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) // If socket for outgoing connection could not be created...
    {
        //spdlog::error("Could not create socket: "std::strerror(errno));
        return false;
    }

    memset((char *) &m_si_other, 0, m_slen);                    //clear address
    m_si_other.sin_family = AF_INET;                            //set socket family
    m_si_other.sin_port = htons(port);                          //set port

    // do dns request before for m_adress!
    if(inet_aton(address.c_str(), &m_si_other.sin_addr)==0){    //set ip address
        //spdlog::error("Invalid address: "+address+", port: "+std::to_string(port));
        return false;
    }

    std::string payload = msg_data.dump();
    const char* msg = payload.c_str();
    int result = sendto(m_socket, msg, strlen(msg), 0, (struct sockaddr *) &m_si_other, m_slen);  //flag MSG_CONFIRM
    if(result<0){
        std::cout<<"Could not send message: "<<std::strerror(errno)<<std::endl;
        return false;
    }
    return true;
}

bool Telemetry_UDP::add_subscriber(const std::string &addr, const unsigned port, const std::vector<std::string> &subs){
    //check ip address:
    std::string ip = addr;
    if(!msrm_utils::is_valid_ip_address(addr.c_str())){
        ip = msrm_utils::get_ip_by_hostname(addr.c_str()).value_or("none");
    }
    if(!msrm_utils::is_valid_ip_address(ip.c_str())){
        spdlog::error("Invalid IP address " + addr + " set for telemetry.");
        return false;
    }
    // is subscriber already in subscriber list?
    Subscriber sub_temp = {port, ip, addr, subs};
    auto it = std::find_if(subscriber_vector.begin(), subscriber_vector.end(), 
             [&ip_temp = addr]
             (const Subscriber &sub) -> bool { return ip_temp == sub.address; }); 
    if(it == subscriber_vector.end()){
        subscriber_vector.push_back(sub_temp);  //add new subscriber
    }
    else{  //update subscriber
        for(auto sub : subscriber_vector){
            if(sub.address == sub_temp.address){
                sub.subscribtions = sub_temp.subscribtions;
                sub.port = sub_temp.port;
            }
        }
    }

    bool result = Telemetry_UDP::start_sending();

    return result;
}
bool Telemetry_UDP::start_sending(){
    //start sending_loop in own thread
    spdlog::debug("Telemetry_UDP.start_sending "+std::to_string(keep_running));
    if(keep_running){
        return true;
    }
    keep_running = true;
    sending_thread = std::thread(&Telemetry_UDP::sending_loop, this);
    return true;

}
bool Telemetry_UDP::stop_sending(){
// keep running false, join running thread
    keep_running = false;
    sending_thread.join();
    return true;
}
void Telemetry_UDP::sending_loop(){
    spdlog::debug("Telemetry_UDP.sending_loop started");
    while(keep_running){
        //get current percept
        if(!m_core->refresh_percept({})){
            spdlog::error("No current state available, could not refresh perception.");
        }
        const Percept* p = m_core->get_percept();
        nlohmann::json msg_data;

        msrm_utils::write_json_array<double,7,1>(msg_data["tau_ext"],p->proprioception.tau_ext);
        msrm_utils::write_json_array<double,7,1>(msg_data["q"],p->proprioception.q);
        msrm_utils::write_json_array<double,4,4>(msg_data["O_T_EE"],p->proprioception.O_T_EE);
        
        //send udp messages to all subscribers
        int count = subscriber_vector.size();
        for(auto sub : subscriber_vector){
            bool works = send(msg_data, sub.ip, sub.port);
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(m_frequency));
    }
}


}
