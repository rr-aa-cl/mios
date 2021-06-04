#include "panda/softhand2.hpp"
#include <spdlog/spdlog.h>


namespace mios{

Softhand2::Softhand2(const char *port_s, int device_id, int BAUD_RATE):m_port_s(port_s),m_device_id(device_id),m_baudrate(BAUD_RATE){

}

Softhand2::~Softhand2(){
    closeRS485(&m_settings);
}

bool Softhand2::initialize(){
    spdlog::debug("qb SoftHand Initialization");
    char serial_ports[10][255];
    int serial_ports_count = RS485listPorts(serial_ports);
    if (serial_ports_count <= 0) {
        spdlog::error("Softhand2: no serial port found");
        return false;
    }
    for (int i=0; i<serial_ports_count; i++) {
//        spdlog::debug("Softhand: serial port "+std::to_string(int(serial_ports[i]))+" found.");
    }
    openRS485(&m_settings, m_port_s, m_baudrate); // use one of the values from RS485listPorts
    if (m_settings.file_handle == INVALID_HANDLE_VALUE) {
//        spdlog::error("fails while opening the serial resource (sets errno [" +std::to_string(int(strerror(errno)))+ "]).");
        spdlog::error("Please add your username to group dialout to acquire the access right to serial ports");
        spdlog::error("Example command in terminal: sudo adduser username dialout");
        spdlog::error("Then reboot for this to take effect");
        return false;
    }
    commActivate(&m_settings, m_device_id, true); //activate motor
    usleep(10000);
    char status;
    int result = commGetActivate(&m_settings, m_device_id, &status);
    spdlog::debug("Robot Hand Status: "+std::to_string(int(status)));
    if (result != 0 || status == 0) {
        spdlog::error("ERROR: fails while activating motor");
        return false;
    }
    short int currents[2]; // only the first value is meaningful
    short int positions[3]; // only the first value is meaningful
    if (commGetMeasurements(&m_settings, m_device_id, positions) < 0) {
        spdlog::error("ERROR: fails while retrieving motor position");
        return false;
    }
    if(commGetCurrents(&m_settings,m_device_id, currents)<0){
        spdlog::error("ERROR: fails while retrieving motor currents");
        return false;
    }
    spdlog::debug("Softhand : motor position is " +std::to_string(positions[0]));
    spdlog::debug("Softhand: motor current is " + std::to_string(currents[0]));

    spdlog::debug("qbSoftHand Initialization Successful");
    return true;
}

bool Softhand2::move(double position){
    std::cout<<"MOVE"<<std::endl;
    short int commands[2];
    if(position>1) position=1;
    if(position<0) position=0;
    commands[0] = static_cast<int>(position*19000);
    commands[1] = 0;
    commSetInputs(&m_settings, m_device_id, commands);
    usleep(500000);
    char status;
    return true;
}

}
