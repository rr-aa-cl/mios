#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <string.h>

#include "spdlog/spdlog.h"
#include "spdlog/sinks/basic_file_sink.h"
#include "spdlog/sinks/stdout_color_sinks.h"

#include "pybind11/pybind11.h"
#include "mios/core/core.hpp"
#include "mirmi_cpp_utils/network/network.hpp"
#include "cxxopts.hpp"
#include "commons/config.hpp"

void exit_handler(int s);


int main(int argc, char** argv){

    cxxopts::Options options("MIOS", "Machine Intelligence Operating System");
    options.add_options()
            ("v,verbosity","Set level of verbosity.",cxxopts::value<std::string>()->default_value("info"))
            ("p,database_port","Port of mongodb database.",cxxopts::value<unsigned>()->default_value("27017"))
            ("c,robot_config","Initial configuration of robot: 0 - arm and Franka Hand, 1 - only arm, 2 - arm and Softhand2, 3 - no arm and gripper.",cxxopts::value<unsigned>()->default_value("0"))
            ("a,robot_arm", "left arm or right arm", cxxopts::value<std::string>()->default_value("left"));

    auto result = options.parse(argc, argv);
    std::string verbosity=result["v"].as<std::string>();
    unsigned database_port=result["p"].as<unsigned>();
    unsigned robot_configuration=result["c"].as<unsigned>();
    std::string robot_arm = result["a"].as<std::string>();

    spdlog::level::level_enum info_level;
    if(verbosity=="trace"){
        info_level=spdlog::level::trace;
    }else if(verbosity=="debug"){
        info_level=spdlog::level::debug;
    }else if(verbosity=="info"){
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
    sigaction(SIGINT, &sigIntHandler, NULL);

    spdlog::info("############################################################");
    spdlog::info("MIOS");
    spdlog::info("Version: " + std::to_string(PROJECT_VERSION_MAJOR) + "." + std::to_string(PROJECT_VERSION_MINOR) + "." + std::to_string(PROJECT_VERSION_PATCH));

    unsigned port = (robot_arm == "left")? 12000 : 13000;
    if(!mirmi_utils::is_port_available("localhost",port)){
        spdlog::error("Port "+std::to_string(port)+" is blocked by another process. You can check which process is blocking the port"
                                                   "by typing 'netstat -ntlup | grep "+std::to_string(port)+"' in a terminal. Terminating...");
        return -1;
    }

    std::string RosName = (robot_arm == "left")? "miosL" : "miosR";
    //ros::init(argc, argv, RosName, ros::init_options::NoSigintHandler);

    pybind11::scoped_interpreter guard{};
    mios::Core core(database_port,robot_configuration, robot_arm);
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

void exit_handler(int s){
    printf("Caught exit signal %i, terminating server.",s);
    exit(0);
}
