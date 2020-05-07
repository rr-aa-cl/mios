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

#include <msrm_utils/system.hpp>
#include <msrm_utils/network.hpp>

void exit_handler(int s);


int main(int argc, char** argv){

    struct sigaction sigIntHandler;

    sigIntHandler.sa_handler = exit_handler;
    sigemptyset(&sigIntHandler.sa_mask);
    sigIntHandler.sa_flags = 0;
    sigaction(SIGINT, &sigIntHandler, NULL);

    unsigned port=8383;
    if(!msrm_utils::is_port_available("localhost",port)){
        msrm_utils::print_error("Port "+std::to_string(port)+" is blocked by another process. You can check which process is blocking the port"
                         "by typing 'netstat -ntlup | grep "+std::to_string(port)+"' in a terminal. Terminating...");
        return -1;
    }

    msrm_utils::print_info("############################################################");
    msrm_utils::print_info("MIOS");
    msrm_utils::print_info("Version: 0.4.1.0");

    mios::Interface interface(port);
    mios::ParameterServer live_params(port+1);
    mios::Core core(argc,argv);
    mios::TaskHandler task_handler(&core);
    interface.initialize(&core,&task_handler);
    interface.start();
    live_params.initialize();
    live_params.start();
    core.set_live_parameter_server(&live_params);

    msrm_utils::print_info("############################################################");
    msrm_utils::print_info("System is ready.");
    task_handler.activity();
    interface.stop();
    live_params.stop();
    return 0;
}

void exit_handler(int s){
    printf("Caught exit signal %i, terminating server.",s);
    exit(0);
}
