#include "telemetry/telemetry_udp.hpp"

#include "cpp_utils/network.hpp"

namespace mios {

Telemetry_UDP::Telemetry_UDP(){

}

Telemetry_UDP::~Telemetry_UDP(){

}

bool Telemetry_UDP::initialize(ConfigTelemetryUDP config){
    this->_config=config;
    this->_n_package=0;
    this->_cnt_frequency=0;

    std::string ip=this->_config.ip_dst;
    if(!cpp_utils::is_valid_ip_address(this->_config.ip_dst.c_str())){
        ip=cpp_utils::get_ip_by_hostname(this->_config.ip_dst);
    }

    this->_slen_out=sizeof(this->_si_other_out);

    if ((this->_s_out=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        cpp_utils::print_error("Initialization of outgoing connection failed.");
        return false;
    }

    if(!cpp_utils::is_valid_ip_address(ip.c_str())){
        cpp_utils::print_error("Invalid IP address " + this->_config.ip_dst + " set for telemetry.");
        return false;
    }

    memset((char *) &this->_si_other_out, 0, sizeof(this->_si_other_out));
    this->_si_other_out.sin_family = AF_INET;
    this->_si_other_out.sin_port = htons(this->_config.port_dst);
    inet_aton(this->_config.ip_dst.c_str(), &this->_si_other_out.sin_addr);

    return true;
}

bool Telemetry_UDP::send_telemetry(const Percept &p){

    this->_cnt_frequency++;
    if(this->_cnt_frequency>=(ceil(1000.0/this->_config.frequency))){
        this->_cnt_frequency=0;
    }else{
        return true;
    }

    char msg[this->_config.packagesize];

    for(unsigned i=0;i<this->_config.packagesize;i++){
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
        q_union.f = (float)p.q[i];
        msg[cnt_byte++]=q_union.bytes[0];
        msg[cnt_byte++]=q_union.bytes[1];
        msg[cnt_byte++]=q_union.bytes[2];
        msg[cnt_byte++]=q_union.bytes[3];
    }
    for(unsigned i=0;i<7;i++){
        q_union.f = (float)p.dq[i];
        msg[cnt_byte++]=q_union.bytes[0];
        msg[cnt_byte++]=q_union.bytes[1];
        msg[cnt_byte++]=q_union.bytes[2];
        msg[cnt_byte++]=q_union.bytes[3];
    }
    for(unsigned i=0;i<7;i++){
        q_union.f = (float)p.tau_ext[i];
        msg[cnt_byte++]=q_union.bytes[0];
        msg[cnt_byte++]=q_union.bytes[1];
        msg[cnt_byte++]=q_union.bytes[2];
        msg[cnt_byte++]=q_union.bytes[3];
    }
    for(unsigned i=0;i<4;i++){
        for(unsigned j=0;j<4;j++){
            q_union.f = (float)p.O_T_EE(j,i);
            msg[cnt_byte++]=q_union.bytes[0];
            msg[cnt_byte++]=q_union.bytes[1];
            msg[cnt_byte++]=q_union.bytes[2];
            msg[cnt_byte++]=q_union.bytes[3];
        }
    }
    for(unsigned i=0;i<6;i++){
        q_union.f = (float)p.K_F_ext(i);
        msg[cnt_byte++]=q_union.bytes[0];
        msg[cnt_byte++]=q_union.bytes[1];
        msg[cnt_byte++]=q_union.bytes[2];
        msg[cnt_byte++]=q_union.bytes[3];
    }

    float E=p.dq.transpose()*p.M*p.dq;

    q_union.f = (float)E;
    msg[cnt_byte++]=q_union.bytes[0];
    msg[cnt_byte++]=q_union.bytes[1];
    msg[cnt_byte++]=q_union.bytes[2];
    msg[cnt_byte++]=q_union.bytes[3];

    for(unsigned i=0;i<32;i++){
        if(i<p.mios_state.active_task.size()){
            msg[cnt_byte++]=p.mios_state.active_task[i];
        }else{
            msg[cnt_byte++]=0;
        }
    }

    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;

    assert(cnt_byte==this->_config.packagesize);
    int err=sendto(this->_s_out, msg, sizeof(msg) , 0 , (struct sockaddr *) &this->_si_other_out, this->_slen_out)<0;
    if(err<0){
        cpp_utils::print_error("Could not send package.");
        return false;
    }
    return true;
}

bool Telemetry_UDP::terminate(){
    int r=close(this->_s_out);
    if(r<0){
        return false;
    }
    return true;
}


}
