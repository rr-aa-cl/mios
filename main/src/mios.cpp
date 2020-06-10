#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <string.h>

#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>
#include <spdlog/sinks/stdout_color_sinks.h>

#include "core/core.hpp"

#include <msrm_utils/network.hpp>

void exit_handler(int s);


int main(int argc, char** argv){
    std::cout<<"FIRST LINE OF CODE"<<std::endl;

    struct sigaction sigIntHandler;

    sigIntHandler.sa_handler = exit_handler;
    sigemptyset(&sigIntHandler.sa_mask);
    sigIntHandler.sa_flags = 0;
    sigaction(SIGINT, &sigIntHandler, NULL);


    spdlog::info("############################################################");
    spdlog::info("MIOS");
    spdlog::info("Version: 0.6.0.0");

    unsigned port=12000;
    if(!msrm_utils::is_port_available("localhost",port)){
        spdlog::error("Port "+std::to_string(port)+" is blocked by another process. You can check which process is blocking the port"
                         "by typing 'netstat -ntlup | grep "+std::to_string(port)+"' in a terminal. Terminating...");
        return -1;
    }

    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    console_sink->set_level(spdlog::level::debug);
    console_sink->set_pattern("[mios] [%^%l%$] %v");

    auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>("logs/mios.txt", true);
    file_sink->set_level(spdlog::level::debug);

    auto logger = std::shared_ptr<spdlog::logger>(new spdlog::logger("mios", {console_sink, file_sink}));
    logger->set_level(spdlog::level::debug);
    spdlog::set_default_logger(logger);

    ros::init(argc, argv, "mios", ros::init_options::NoSigintHandler);

    mios::Core core;
    if(!core.initialize()){
        spdlog::error("MIOS core could not be initialized, shutting down...");
        return -1;
    }
    spdlog::info("############################################################");
    spdlog::info("System is ready.");
    core.get_task_engine()->life_cycle();
    spdlog::debug("LAST LINE OF CODE");
    return 0;
}

void exit_handler(int s){
    printf("Caught exit signal %i, terminating server.",s);
    exit(0);
}
