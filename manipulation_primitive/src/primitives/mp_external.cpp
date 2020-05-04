#include "primitives/mp_external.hpp"

#include <msrm_utils/math.hpp>
#include <msrm_utils/conversion.hpp>
#include <msrm_utils/network.hpp>

namespace mios {

mp_external::mp_external():ManipulationPrimitive("mp_external"){
    this->_eval = std::make_shared<EvalMP_mp_external>();
    this->_config = std::make_shared<ConfigMP_mp_external>();
    this->_attractor= std::make_shared<AttractorExternal>();
    this->_bufferlength=512;
    this->_flag_connected=false;
    this->_flag_run=false;
    this->_flag_return_state=true;
}

void mp_external::initialize(const Percept &p_0, const std::shared_ptr<ConfigUser> config){
    std::shared_ptr<ConfigMP_mp_external> c_mp = std::static_pointer_cast<ConfigMP_mp_external>(this->_config);
    this->_flag_init=false;
    this->_n_package=0;
    this->_n_package_last=0;
    this->_cnt_send=0;
    this->_send_msg_at_n = (int)(1000/c_mp->input_frequency);

    this->initialize_connections();

    this->_cmd.q_d=p_0.q;
    this->_q_d_in[0]=msrm_utils::convert_to_array<double,7,1>(p_0.q);
    this->_O_T_EE_d_in[0]=msrm_utils::convert_to_array<double,4,4>(p_0.O_T_EE);
    this->_dq_d_in[0]={0,0,0,0,0,0,0};
    this->_dX_d_in[0]={0,0,0,0,0,0};
    this->_tau_in[0]={0,0,0,0,0,0,0};

    this->_flag_sync=false;
}

CmdMP& mp_external::step(const Percept &p){
    std::shared_ptr<ConfigMP_mp_external> c_mp = std::static_pointer_cast<ConfigMP_mp_external>(this->_config);

    if(c_mp->mode==InputMode::Torque){
        this->_cmd.tau_ff=Eigen::Matrix<double,7,1>(this->_tau_in[0].data());
    }
    if(c_mp->mode==InputMode::CartesianVelocity){
        this->_cmd.TF_dX_d=Eigen::Matrix<double,6,1>(this->_dX_d_in[0].data());
    }
    if(c_mp->mode==InputMode::JointVelocity){
        this->_cmd.dq_d=Eigen::Matrix<double,7,1>(this->_dq_d_in[0].data());
    }
    if(c_mp->mode==InputMode::CartesianPosition){
        this->_cmd.TF_T_EE_d=Eigen::Matrix<double,4,4>(this->_O_T_EE_d_in[0].data());
    }
    if(c_mp->mode==InputMode::JointPosition){
        this->_cmd.q_d=Eigen::Matrix<double,7,1>(this->_q_d_in[0].data());
    }
    if(this->_flag_return_state){
        std::vector<double> payload;
        payload.reserve(21);
        for(unsigned i=0;i<7;i++){
            payload.push_back(p.q(i));
        }
        for(unsigned i=0;i<7;i++){
            payload.push_back(p.dq(i));
        }
        for(unsigned i=0;i<7;i++){
            payload.push_back(p.tau_ext(i));
        }
        this->msg_out(payload);
        this->_flag_return_state=false;
    }
    return this->_cmd;
}

void mp_external::terminate(){
    if(this->_thr_msg_in.joinable()){
        this->_flag_run=false;
    }
}

bool mp_external::check_attractor(){
    return true;
}

bool mp_external::init_attractor(const Percept &p, const std::shared_ptr<ConfigUser> config){
    return true;
}

bool mp_external::in_attractor(const Percept &p){
    return true;
}

void mp_external::setup_logs(unsigned long long length){

}

void mp_external::write_logs(){

}

bool mp_external::initialize_connections(){
    std::shared_ptr<ConfigMP_mp_external> config = std::static_pointer_cast<ConfigMP_mp_external>(this->_config);
    // Initialize member variables
    this->_flag_connected=false;
    this->_n_package=0;
    this->_n_package_last=0;
    this->_bufferlength=256;

    std::string ip_dst;

    // If a hostname instead of IP is provided, it is converted to an IP
    if(!msrm_utils::is_valid_ip_address(config->ip_dst.c_str())){
        ip_dst=msrm_utils::get_ip_by_hostname(config->ip_dst.c_str()).value_or("none");
    }else{
        ip_dst=config->ip_dst;
    }

    if(!msrm_utils::is_valid_ip_address(ip_dst.c_str())){ // If IP is not valid...
        msrm_utils::print_error("Invalid ip: "+ip_dst);
        return false;
    }

    // Setup of outgoing connection
    this->_slen_out=sizeof(this->_si_other_out);
    if ((this->_s_out=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) // If socket for outgoing connection could not be created...
    {
        msrm_utils::print_error("Initialization of outgoing connection failed.");
        return false;
    }
    memset((char *) &this->_si_other_out, 0, sizeof(this->_si_other_out));
    this->_si_other_out.sin_family = AF_INET;
    this->_si_other_out.sin_port = htons(config->port_dst);
    inet_aton(ip_dst.c_str(), &this->_si_other_out.sin_addr);
    // Outgoing connection was properly created.

    // Incoming connection
    this->_slen_in = sizeof(this->_si_other_in);
    if((this->_s_in=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1){ // If socket for incoming connection could not be created...
        msrm_utils::print_error("Initialization of incoming connection failed.");
        return false;
    }

    // Set timeout of 10 ms for incoming UDP connection
    //    struct timeval tv;
    //    tv.tv_sec = 0;
    //    tv.tv_usec = (int)(1./config->input_frequency*1000000);
    //    setsockopt(this->_s_in, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);

    memset((char *) &this->_si_me_in, 0, sizeof(this->_si_me_in));
    this->_si_me_in.sin_family = AF_INET;
    this->_si_me_in.sin_port = htons(config->port_recv);
    this->_si_me_in.sin_addr.s_addr=htonl (INADDR_ANY);
    bind(this->_s_in , (struct sockaddr*)&this->_si_me_in, sizeof(this->_si_me_in));

    this->_flag_run=true;
    this->_thr_msg_in=std::thread(&mp_external::msg_in,this);
    this->_thr_msg_in.detach();

    // Incoming connection was properly created.

    msrm_utils::print_info("Incoming connection configured with port: "+std::to_string(config->port_recv));

    return true;
}

void mp_external::msg_in() {

    // Buffer is initialized
    char buf[this->_bufferlength];

    // Variables are initialized
    bool lost_package=false;
    bool msg_corrupt=false;
    bool msg_buffer=false;
    bool msg_connection_wait=false;
    bool msg_connection_valid=false;
    bool msg_connection_lost=false;
    this->_flag_valid_package=false;
    this->_cnt_lost_packages=0;
    unsigned cnt_no_connection=0;
    unsigned payload_size=0;
    // Header size of message (contains 4 start bytes, 4 end bytes, 1 package counter, 1 payload size, naming is not quite correct)
    unsigned header_size=10;

    // Loop for incoming messages is started
    while(true) { // Runs forever if no errors occur...
        if(!this->_flag_run){ // If an interrupt exception occurs...
            msrm_utils::print_info("Incoming communication terminated.");
            int r=close(this->_s_in); // Socket is closed
            if(r<0){ // If an error occured during socket termination...
                msrm_utils::print_error("Could not close socket.");
            }
            return;
        }
        if(!msg_connection_wait){
            msrm_utils::print_info("Waiting for incoming messages...");
            msg_connection_wait=true;
        }
        // Current content from the UDP connection is read into the buffer
        int reclen=recvfrom(this->_s_in, buf, this->_bufferlength, 0, (struct sockaddr *) &this->_si_me_in, &this->_slen_in);
        if(reclen<0 && this->_flag_connected){ // If connection is already established but the received message is invalid...
            cnt_no_connection++;
        }

        char* msg = buf;

        lost_package=true;
        unsigned i=0;
        for(i;i<this->_bufferlength;i++){ // For every element in the message
            if(msg[i]==127 && msg[i+1]==127 && msg[i+2]==127 && msg[i+3]==127){ // If start bytes have been found...
                payload_size=(unsigned)msg[i+5]; // Read payload size
                if(msg[i+payload_size+header_size-4]==126 && msg[i+payload_size+header_size-3]==126 && msg[i+payload_size+header_size-2]==126 && msg[i+payload_size+header_size-1]==126){ // If end bytes have been found in accordance with the payload size
                    lost_package=false; // A valid message has been found.
                    break;
                }
            }
        }
        if(!((int)msg[i+4]==this->_n_package_last+1 || ((int)msg[i+4]==0 && this->_n_package_last==99))){ // If the last package counter is not one less than the current package counter...
            //                msrm_utils::print_warning("I am losing packets.");
        }
        if(i>=this->_bufferlength-payload_size+header_size && reclen==payload_size+header_size && this->_flag_connected){ // If the message cannot fit into the buffer but start bytes have been found...
            if(!msg_buffer){
                msrm_utils::print_warning("Message reaches over end of buffer. Start of message is "+std::to_string(i)+".");
                msg_buffer=true;
            }
            cnt_no_connection++;
            lost_package=true;
        }
        if(reclen!=payload_size+header_size && this->_flag_connected){ // If the length of the received message is not equal to required message size and connection has already been established...
            if(!msg_corrupt){
                msrm_utils::print_warning("Corrupted message. Received length is "+std::to_string(reclen) + ". Expected length is "+std::to_string(payload_size+header_size)+".");
                msg_corrupt=true;
            }
            cnt_no_connection++;
            lost_package=true;
        }
        if(cnt_no_connection>0 && !lost_package){ // If packages have been lost and the current one is valid...
            msrm_utils::print_warning("Number of lost packages: "+std::to_string(this->_cnt_lost_packages));
            cnt_no_connection=0;
            msg_buffer=false;
            msg_corrupt=false;
        }
        this->_n_package_last=(int)msg[i+4]; // Read the package counter

        if(cnt_no_connection>20){ // If 20 packages were invalid after a connection has already been established...
            if(!msg_connection_lost){
                msrm_utils::print_critical_error("Lost 20 packets in a row. I assume the network connection is faulty and will terminate.");
                msg_connection_lost=true;
            }
            this->set_flag_error(); // Terminate prototype
        }
        if(lost_package){ // If a package was lost...
            usleep(1000); // Sleep for 1 ms
            this->_flag_valid_package=false; // Indicate an invalid package
            continue;
        }else{
            this->_flag_connected=true; // The first time this line is reached, a connection is considered as established.
            this->_flag_valid_package=true; // Indicate a valid package
            if(!msg_connection_valid){
                msrm_utils::print_info("Communication has been established.");
                msg_connection_valid=true;
            }
        }
        std::vector<double> payload;
        // Use a union to convert the bytes in the message into doubles.
        union {
            float f;
            char bytes[4];
        } q_union;
        // Read payload
        payload.reserve(payload_size/4);
        for(unsigned j=0;j<payload_size;j+=4){ // For every 4 bytes in the message...
            q_union.bytes[0]=msg[i+j+6];
            q_union.bytes[1]=msg[i+j+7];
            q_union.bytes[2]=msg[i+j+8];
            q_union.bytes[3]=msg[i+j+9];
            payload[j/4]=(q_union.f); // Converted data element is pushed into the payload vector
        }
        // Unload the payload. This function has to be defined by the respective telepresence prototype.
        if(this->unload_msg(payload)){
            this->_flag_return_state=true;
        }

    }
}

bool mp_external::msg_out(const std::vector<double> &payload){
    // Determine package size: Size of payload * 4 (4 bytes per double) + 4 start bytes + 4 end bytes + package counter + size of payload
    unsigned package_size=payload.size()*4+10;

    // Initialize message container and set content to zero.
    char msg[package_size];
    for(unsigned i=0;i<package_size;i++){
        msg[i]=0;
    }

    // Elements of message are assigned in a sequence, the counter (cnt_byte) is automatically incremented after each assignment via the increment operator ++
    unsigned cnt_byte=0;

    // The first 4 bytes are start bytes, they are used to identify the message.
    msg[cnt_byte++]=127;
    msg[cnt_byte++]=127;
    msg[cnt_byte++]=127;
    msg[cnt_byte++]=127;

    // Via the package counter one can check if packages have been lost.
    msg[cnt_byte++]=this->_n_package;
    this->_n_package++;
    if(this->_n_package>=100){ // If the package counter reaches 100, it is reset to 0...
        this->_n_package=0;
    }

    // The payload size tells the receiver where to find the end bytes and how much to copy.
    msg[cnt_byte++]=payload.size()*4;

    // A union is used to convert the doubles in the payload into bytes that can be sent via UDP.
    union {
        float f;
        char bytes[4];
    } q_union;
    // Every element is converted into 4 bytes (1 double = 4 bytes of memory)
    for(unsigned i=0;i<payload.size();i++){ // For every element in the payload...
        q_union.f = (float)payload[i];
        msg[cnt_byte++]=q_union.bytes[0];
        msg[cnt_byte++]=q_union.bytes[1];
        msg[cnt_byte++]=q_union.bytes[2];
        msg[cnt_byte++]=q_union.bytes[3];
    }
    // The end bytes are used to completely identify the message on the receiver side.
    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;
    msg[cnt_byte++]=126;

    // The message is sent out to the peer robot.
    int err=sendto(this->_s_out, msg, sizeof(msg) , 0 , (struct sockaddr *) &this->_si_other_out, this->_slen_out)<0;
    if(err<0){ // If an error occured during sending...
        msrm_utils::print_error("Could not send package.");
        return false; // The prototype is terminated.
    }
    return true;
}

bool mp_external::unload_msg(const std::vector<double> &payload){
    std::shared_ptr<ConfigMP_mp_external> c_mp = std::static_pointer_cast<ConfigMP_mp_external>(this->_config);
    if(c_mp->mode==InputMode::Torque){
        if(payload.size()!=7){
            msrm_utils::print_error("Payload size is " + std::to_string(payload.size()) + " but expected is 7.");
            return false;
        }
        for(unsigned i=0;i<7;i++){
            this->_tau_in[0][i]=payload[i];
        }
    }
    if(c_mp->mode==InputMode::CartesianVelocity){
        if(payload.size()!=6){
            msrm_utils::print_error("Payload size is " + std::to_string(payload.size()) + " but expected is 6.");
            return false;
        }
        for(unsigned i=0;i<6;i++){
            this->_dX_d_in[0][i]=payload[i];
        }
    }
    if(c_mp->mode==InputMode::JointVelocity){
        if(payload.size()!=7){
            msrm_utils::print_error("Payload size is " + std::to_string(payload.size()) + " but expected is 7.");
            return false;
        }
        for(unsigned i=0;i<7;i++){
            this->_dq_d_in[0][i]=payload[i];
        }
    }
    if(c_mp->mode==InputMode::CartesianPosition){
        if(payload.size()!=16){
            msrm_utils::print_error("Payload size is " + std::to_string(payload.size()) + " but expected is 16.");
            return false;
        }
        for(unsigned i=0;i<7;i++){
            this->_O_T_EE_d_in[0][i]=payload[i];
        }
    }
    if(c_mp->mode==InputMode::JointPosition){
        if(payload.size()!=7){
            msrm_utils::print_error("Payload size is " + std::to_string(payload.size()) + " but expected is 7.");
            return false;
        }
        for(unsigned i=0;i<7;i++){
            this->_q_d_in[0][i]=payload[i];
        }
    }
    return true;
}

}
