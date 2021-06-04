#pragma once

#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sstream>
#include <deque>
#include <poll.h>
#include <atomic>
#include <unistd.h>
#include <vector>
#include <string>
#include <thread>
#include <mutex>
#include <map>
#include <nlohmann/json.hpp>

namespace msrm_utils{
class UDPStreamSender;
}


namespace mios {

class Core;
class Portal;

struct Subscriber{
    unsigned port;
    std::string ip;
    std::string address;
    std::vector<std::string> subscriptions;
    bool sendWithTerminatingNullCharacter;
    std::shared_ptr<msrm_utils::UDPStreamSender> stream;
};

class TelemetryUDP{
public:
    TelemetryUDP(Core* core, Portal* portal);
    ~TelemetryUDP();

    bool add_subscriber(const std::string &addr, unsigned port, const std::vector<std::string> &subs,
                        bool sendWithTerminatingNullCharacter);
    bool remove_subscriber(const std::string &addr);
    bool start_sending();
    bool stop_sending();
    
private:
    bool send(const nlohmann::json &msg_data, const std::string &address, const unsigned port);
    void sending_loop();

    Core* m_core;
    Portal* m_portal;

    std::vector<Subscriber> m_subscribers;
    std::atomic<bool> m_keep_running;
    std::thread m_thr_send;
    bool m_thread_running;
    std::mutex m_mtx_subscriber;

    unsigned m_frequency;  //ms
    std::chrono::time_point<std::chrono::high_resolution_clock> m_time_1;
    std::chrono::time_point<std::chrono::high_resolution_clock> m_time_2;
    std::chrono::duration<double, std::milli> m_time_duration;

    std::map<std::string, unsigned> m_data_map{
                    //End effector pose in origin frame (O).
                        {"O_T_EE", 1},
                    //End effector pose in task frame (TF).
                        {"T_T_EE", 2},
                    //Link-side joint pose.
                        {"q", 3},
                    //Link-side joint velocities.
                        {"dq", 4},
                    //Motor-side joint pose.
                        {"theta", 5},
                    //Motor-side joint velocities.
                        {"dtheta", 6},
                    //Cartesian twist in origin frame (O).
                        {"O_dX_EE", 7},
                    //Cartesian twist in end effector frame (EE).
                        {"EE_dX_EE", 8},
                    //Cartesian twist in task frame (TF).
                        {"TF_dX_EE", 9},
                    //Estimated external torques.
                        {"tau_ext", 10},
                    //Joint torques.
                        {"tau_j", 11},
                    //Estimated external wrench at TCP in stiffness frame (K).
                        {"K_F_ext_K", 12},
                    //Derivative of estimated external wrench at TCP in stiffness frame (K).
                        {"K_dF_ext_K", 13},
                    //Estimated external wrench at TCP in origin frame (O).
                        {"O_F_ext_K", 14},
                    //Derivative of estimated external wrench at TCP in origin frame (O).
                        {"O_dF_ext_K", 15},
                    //Estimated external wrench at TCP in task frame (TF).
                        {"TF_F_ext_K", 16},
                    //Derivative of estimated external wrench at TCP in task frame (TF).
                        {"TF_dF_ext_K", 17},

                        {"finger_width", 18},
                        {"finger_temperature", 19},
                        {"is_grasping", 20},

                    //Mass matrix.
                        {"M", 21},
                    //Coriolis vector.
                        {"C", 22},
                    //Gravity vector.
                        {"G", 23},
                    //Body jacobian.
                        {"B_J_EE",24},
                    //Zero jacobian. 
                        {"B_J_O", 25},

                        {"max_finger_width", 26},
                        {"hand_activity_state", 27},

                    //Rho factor from force controllers's shaping function.
                        {"e", 28},
                        {"rho", 29},

                        {"K_x", 30},
                        {"xi_x", 31},
                        {"K_theta", 32},
                        {"xi_theta", 33},
                
                        {"TF_T_EE_d", 34},
                        {"TF_dX_d", 35},
                        {"TF_F_ff", 36},
                        {"O_R_T", 37},

                        {"q_d", 38},
                        {"dq_d", 39},
                        {"tau_ff", 40}
    };

};

}
