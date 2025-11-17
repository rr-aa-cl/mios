#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <string.h>

#include "spdlog/spdlog.h"
#include "spdlog/sinks/basic_file_sink.h"
#include "spdlog/sinks/stdout_color_sinks.h"
#include "spdlog/fmt/ostr.h"

#include "pybind11/pybind11.h"
#include "mios/core/core.hpp"
#include "mios/utils/context.hpp"
#include "mios/utils/configuration.hpp"
#include "mirmi_cpp_utils/network/network.hpp"
#include "cxxopts.hpp"
#include "commons/config.hpp"

// Global control flags
std::atomic<bool> shutdown_signal{false};
std::atomic<int> signal_count{0};

void exit_handler(int signum) {
    int count = ++signal_count;
    if (count == 1) {
        // --- FIRST SIGNAL: GRACEFUL ---
        shutdown_signal = true;
        const char* msg = "\n[SIG] Shutdown signal received. Cleaning up...\n"
                          "[SIG] Press Ctrl+C again to FORCE kill immediately.\n";
        write(STDERR_FILENO, msg, 84); 
    } 
    else {
        // --- SECOND SIGNAL: FORCE KILL ---
        const char* msg = "\n[SIG] Force quitting!\n";
        write(STDERR_FILENO, msg, 21);
        std::_Exit(EXIT_FAILURE); 
    }
}

int main(int argc, char** argv){

    cxxopts::Options options("MIOS", "Machine Intelligence Operating System");
    options.add_options()
            ("v,verbosity","Set level of verbosity.",cxxopts::value<std::string>()->default_value("info"))
            ("p,database_port","Port of mongodb database.",cxxopts::value<unsigned>()->default_value("27017"))
            ("n,database_name","Name of mongodb database.",cxxopts::value<std::string>()->default_value("mios"))
            ("i,robot_ip","IPv4 of Robot ControlBox.",cxxopts::value<std::string>()->default_value("127.0.0.1"))
            ("w,websocket_port","WebSocket Interface Port used by mios.",cxxopts::value<unsigned>()->default_value("12000"))
            ("r,rpc_port","RPC Interface Port used by mios.",cxxopts::value<unsigned>()->default_value("12001"))
            ("u,udp_port","UDP Interface Port used by mios.",cxxopts::value<unsigned>()->default_value("12002"))
            ("c,robot_config","Initial configuration of robot: 0 - arm and Franka Hand, 1 - only arm, 2 - arm and Softhand2, 3 - no arm and gripper",cxxopts::value<unsigned>()->default_value("0"))
            ("d,desk","Disable DESK interface usage",cxxopts::value<std::string>()->default_value("true"));


    auto result = options.parse(argc, argv);
    mios::MiosConfiguration configuration;
    configuration.verbosity=result["v"].as<std::string>();
    configuration.database_port=result["p"].as<unsigned>();
    configuration.database_name=result["n"].as<std::string>();
    configuration.robot_ip=result["i"].as<std::string>();
    configuration.robot_configuration=result["c"].as<unsigned>();
    configuration.rpc_port=result["r"].as<unsigned>();
    configuration.udp_port=result["u"].as<unsigned>();
    configuration.websocket_port=result["w"].as<unsigned>();
    std::string use_desk = result["d"].as<std::string>();
    configuration.use_desk=(use_desk == "true" || use_desk == "True" || use_desk == "1");

    spdlog::level::level_enum info_level;
    if(configuration.verbosity=="trace"){
        info_level=spdlog::level::trace;
    }else if(configuration.verbosity=="debug"){
        info_level=spdlog::level::debug;
    }else if(configuration.verbosity=="info"){
        info_level=spdlog::level::info;
    }else{
        info_level=spdlog::level::info;
    }


    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    console_sink->set_level(info_level);
    console_sink->set_pattern("[mios] [%^%l%$] %v");

    auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>("logs/mios.txt", true);
    file_sink->set_level(spdlog::level::debug);

    auto logger = std::shared_ptr<spdlog::logger>(new spdlog::logger("mios", {console_sink, file_sink}));
    logger->set_level(info_level);
    spdlog::set_default_logger(logger);
    spdlog::trace("FIRST LINE OF CODE");

    struct sigaction sigIntHandler;

    sigIntHandler.sa_handler = exit_handler;
    sigemptyset(&sigIntHandler.sa_mask);
    sigIntHandler.sa_flags = 0;
    sigaction(SIGINT, &sigIntHandler, NULL);    // catch stop signal form crtl+c
    sigaction(SIGTERM, &sigIntHandler, NULL);   // catch stop signal from docker stop

    spdlog::info("############################################################");
    spdlog::info("MIOS");
    spdlog::info("Version: " + std::to_string(PROJECT_VERSION_MAJOR) + "." + std::to_string(PROJECT_VERSION_MINOR) + "." + std::to_string(PROJECT_VERSION_PATCH));
    spdlog::info("Initial configuration:\n{}", configuration);

    if(!mirmi_utils::is_port_available("localhost",configuration.websocket_port)){
        spdlog::error("Port "+std::to_string(configuration.websocket_port)+" is blocked by another process. You can check which process is blocking the port"
                                                   "by typing 'netstat -ntlup | grep "+std::to_string(configuration.websocket_port)+"' in a terminal. Terminating...");
        return -1;
    }

    std::string RosName = configuration.database_name;
    //ros::init(argc, argv, RosName, ros::init_options::NoSigintHandler);

    pybind11::scoped_interpreter guard{};

    MiosContext context { configuration, shutdown_signal };
    mios::Core core(context);
    spdlog::info("Initializing MIOS core...");
    if(!core.initialize()){
        spdlog::error("MIOS core could not be initialized, shutting down...");
        return -1;
    }
    spdlog::info("############################################################");
    spdlog::info("System is ready.");
    core.start();
    spdlog::trace("LAST LINE OF CODE");
    return 0;
}

