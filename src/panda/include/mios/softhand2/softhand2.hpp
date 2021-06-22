#pragma once

#include "mios/softhand2/qbmove_communications.h"

namespace mios{

class Softhand2{
public:
    Softhand2(const char *port_s = "/dev/ttyUSB0", int device_id = 1, int BAUD_RATE = B2000000);
    ~Softhand2();
    bool initialize();
    bool move(double position);
    double get_position();

private:
    comm_settings m_settings;
    const char* m_port_s;
    int m_device_id;
    int m_baudrate;
};

}
