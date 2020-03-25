#include "interface/sim_interface.hpp"

#include "cpp_utils/output.hpp"

namespace mios {

SimInterface::SimInterface(){

}

SimInterface::~SimInterface(){

}

bool SimInterface::connect_to_sim(std::string ip, unsigned port){
    this->_n_package=0;
    this->_n_package_last=0;
    this->_flag_valid=false;
    this->_lost_package=false;
    this->_cnt_lost_packages=0;
    this->_cnt_no_connection=0;

    this->_packagesize_in=200;
    this->_packagesize_out=16;

    // Outgoing connection
    this->_slen_out=sizeof(this->_si_other_out);

    if ((this->_s_out=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        cpp_utils::print_error("Initialization of outgoing simulation connection failed.");
        return false;
    }
    memset((char *) &this->_si_other_out, 0, sizeof(this->_si_other_out));
    this->_si_other_out.sin_family = AF_INET;
    this->_si_other_out.sin_port = htons(port);
    inet_aton(ip.c_str(), &this->_si_other_out.sin_addr);

    // Incoming connection
    this->_slen_in = sizeof(this->_si_other_in);

    if(this->_s_in=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)<0){
        cpp_utils::print_error("Initialization of incoming simulation connection failed.");
        return false;
    }

    struct timeval tv;
    tv.tv_sec = 0;
    tv.tv_usec = 10000;
    if(setsockopt(this->_s_in, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv)<0){
        cpp_utils::print_error("Setting options for incoming simulation connection has failed.");
        return false;
    }

    memset((char *) &this->_si_me_in, 0, sizeof(this->_si_me_in));
    this->_si_me_in.sin_family = AF_INET;
    this->_si_me_in.sin_port = htons(8385);
    this->_si_me_in.sin_addr.s_addr = htonl(INADDR_ANY);
    bind(this->_s_in , (struct sockaddr*)&this->_si_me_in, sizeof(this->_si_me_in));

    return true;
}

bool SimInterface::send_cmd_torques(std::array<double, 7> tau_J_d){
    char msg[this->_packagesize_out];

    for(unsigned i=0;i<this->_packagesize_out;i++){
        msg[i]=0;
    }

    unsigned cnt_byte=0;
    // start bytes
    msg[cnt_byte++]=127;
    msg[cnt_byte++]=127;
    msg[cnt_byte++]=127;
    msg[cnt_byte++]=127;

    msg[cnt_byte++]=this->_n_package;
    this->_n_package++;
    if(this->_n_package>=100){
        this->_n_package=0;
    }

    // n_bytes = 4
    union {
        float f;
        char bytes[4];
    } q_union;
    for(unsigned i=0;i<7;i++){
        q_union.f = (float)tau_J_d[i];
        msg[cnt_byte++]=q_union.bytes[0];
        msg[cnt_byte++]=q_union.bytes[1];
        msg[cnt_byte++]=q_union.bytes[2];
        msg[cnt_byte++]=q_union.bytes[3];
    }

    // end bytes
    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;

    assert(cnt_byte==this->_packagesize_out);
    int err=sendto(this->_s_out, msg, sizeof(msg) , 0 , (struct sockaddr *) &this->_si_other_out, this->_slen_out)<0;
    if(err<0){
        cpp_utils::print_error("Could not send package to simulation.");
        return false;
    }
    return true;
}

bool SimInterface::recv_state(std::array<double, 200> &state){
    int reclen=recvfrom(this->_s_in, this->_buf, this->_bufferlength, 0, (struct sockaddr *) &this->_si_me_in, &this->_slen_in);
    if(reclen<0 && this->_flag_connected){
        this->_cnt_no_connection++;
    }else{
        this->_cnt_no_connection=0;
    }
    if(this->_cnt_no_connection>10){
        cpp_utils::print_critical_error("Lost connection to peer");
        return false;
    }
    //            std::cout<<"len: "<<reclen<<std::endl;
    char* msg = this->_buf;
    // search message by start and end bytes
    unsigned i=0;
    for(i;i<this->_bufferlength;i++){
        if(msg[i]==127 && msg[i+1]==127 && msg[i+2]==127 && msg[i+3]==127
                && msg[i+this->_packagesize_in-4]==126 && msg[i+this->_packagesize_in-3]==126 && msg[i+this->_packagesize_in-2]==126 && msg[i+this->_packagesize_in-1]==126){
            break;
        }
    }
    if(i>=this->_bufferlength-this->_packagesize_in || !((int)msg[i+4]==this->_n_package_last+1 || ((int)msg[i+4]==0 && this->_n_package_last==99)) || reclen!=this->_packagesize_in){
        //                cpp_utils::print_warning("Lost a message.");
        this->_cnt_lost_packages++;
        //                cpp_utils::print_warning("Lost one package. This package has number "+std::to_string((int)msg[i+4])
        //                        +", the last one has number "+std::to_string(this->_n_package_last)+".");
        this->_lost_package=true;
    }else if(this->_cnt_lost_packages>0){
        //                cpp_utils::print_warning("Number of lost packages: "+std::to_string(this->_cnt_lost_packages));
        this->_cnt_lost_packages=0;
    }
    this->_n_package_last=(int)msg[i+4];

    if(this->_lost_package){
        usleep(1000);
        this->_lost_package=false;
        this->_flag_valid=false;
        return true;
    }else{
        this->_flag_valid=true;
        this->_flag_connected=true;
    }

    // Read desired q from buffer
//    for(unsigned j=0;j<7;j++){
//        union {
//            float f;
//            char bytes[4];
//        } q_union;
//        q_union.bytes[0]=msg[i+j*4+5];
//        q_union.bytes[1]=msg[i+j*4+6];
//        q_union.bytes[2]=msg[i+j*4+7];
//        q_union.bytes[3]=msg[i+j*4+8];
//        this->_q_d_in[0][j]=q_union.f;
//    }
//    for(unsigned j=0;j<7;j++){
//        union {
//            float f;
//            char bytes[4];
//        } q_union;
//        q_union.bytes[0]=msg[i+j*4+33];
//        q_union.bytes[1]=msg[i+j*4+34];
//        q_union.bytes[2]=msg[i+j*4+35];
//        q_union.bytes[3]=msg[i+j*4+36];
//        this->_dq_d_in[0][j]=q_union.f;
//    }
//    for(unsigned j=0;j<7;j++){
//        union {
//            float f;
//            char bytes[4];
//        } q_union;
//        q_union.bytes[0]=msg[i+j*4+61];
//        q_union.bytes[1]=msg[i+j*4+62];
//        q_union.bytes[2]=msg[i+j*4+63];
//        q_union.bytes[3]=msg[i+j*4+64];
//        this->_tau_ext_in[0][j]=q_union.f;
//    }
    return true;

}

}
