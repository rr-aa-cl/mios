#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <string.h>

//#include <jsonrpccxx/server.hpp>

#include "core/core.hpp"
#include "task/task_handler.hpp"
//#include "interface/rpc_server.hpp"
#include "interface/interface.hpp"
#include "interface/parameter_server.hpp"

#include "cpp_utils/system.hpp"
#include "cpp_utils/network.hpp"

void exit_handler(int s);


int main(int argc, char** argv){

    struct sigaction sigIntHandler;

    sigIntHandler.sa_handler = exit_handler;
    sigemptyset(&sigIntHandler.sa_mask);
    sigIntHandler.sa_flags = 0;
    sigaction(SIGINT, &sigIntHandler, NULL);

    unsigned port=8383;
    if(!cpp_utils::is_port_open(port)){
        cpp_utils::print_error("Port "+std::to_string(port)+" is blocked by another process. You can check which process is blocking the port"
                         "by typing 'netstat -ntlup | grep "+std::to_string(port)+"' in a terminal. Terminating...");
        return -1;
    }

    cpp_utils::print_info("############################################################");
    cpp_utils::print_info("MIOS");
    cpp_utils::print_info("Version: 0.3.4.0");

    mios::Interface interface;
    std::shared_ptr<mios::ParameterServer> live_params = std::make_shared<mios::ParameterServer>();
    std::shared_ptr<mios::Core> core = std::make_shared<mios::Core>(argc,argv);
    std::shared_ptr<mios::TaskHandler> task_handler= std::make_shared<mios::TaskHandler>(core);
    interface.initialize(core,task_handler,port);
    interface.start();
    live_params->initialize(port+1);
    live_params->start();
    core->set_live_parameter_server(live_params);

    cpp_utils::print_info("############################################################");
    cpp_utils::print_info("System is ready.");
    task_handler->activity();
    interface.stop();
    live_params->stop();
    return 0;
}

void exit_handler(int s){
    printf("Caught exit signal %i, terminating server.",s);
    exit(0);
}
