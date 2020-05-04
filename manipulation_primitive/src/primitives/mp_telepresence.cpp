#include "primitives/mp_telepresence.hpp"

#include <msrm_utils/math.hpp>
#include <msrm_utils/conversion.hpp>
#include <msrm_utils/network.hpp>

namespace mios {

mp_telepresence::mp_telepresence():ManipulationPrimitive("mp_telepresence"){
    this->_eval = std::make_shared<EvalMP_mp_telepresence>();
    this->_config = std::make_shared<ConfigMP_mp_telepresence>();
    this->_attractor= std::make_shared<AttractorTelepresence>();
    this->_bufferlength=512;
    this->_flag_connected=false;
    this->_thread_should_run=false;
}

void mp_telepresence::initialize(const Percept &p_0, const std::shared_ptr<ConfigUser> config){
    std::shared_ptr<ConfigMP_mp_telepresence> c = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->_config);
    this->_flag_init=false;
    this->_flag_joystick_translation=true;
    this->_flag_joystick_rotation=false;
    this->_joystick_selector<<true,true,true,true,true,true;
    this->_n_package=0;
    this->_n_package_last=0;
    this->_cnt_send=0;
    _J_phi.setZero();

    this->_TF_T_EE_0=p_0.TF_T_EE;

    this->_rot_limits=config->phi_limits;;

    this->initialize_connections();

    this->_cmd.q_d=p_0.q;
    this->_q_d_in[0]=msrm_utils::convert_to_array<double,7,1>(p_0.q);
    this->_dq_d_in[0]={0,0,0,0,0,0,0};
    this->_tau_ext_in[0]={0,0,0,0,0,0,0};

    this->_O_T_EE_in[0]=msrm_utils::convert_to_array<double,4,4>(p_0.O_T_EE);
    this->_O_dX_d_in[0]={0,0,0,0,0,0};
    this->_EE_F_ext_in[0]={0,0,0,0,0,0};

    this->_motion_error_u.O_T_EE=p_0.TF_T_EE;
    this->_motion_error_u.O_T_EE_d=p_0.TF_T_EE;

    this->_motion_error_0_u.O_T_EE=p_0.TF_T_EE;
    this->_motion_error_0_u.O_T_EE_d=p_0.TF_T_EE;

    this->_joystick_dX_max<<config->dX_max(0),config->dX_max(0),config->dX_max(0),config->dX_max(1),config->dX_max(1),config->dX_max(1);

    motion_error_cart::In_P_motion_error_cart motion_error_p;
    this->_motion_error.initialize(this->_motion_error_u,motion_error_p);

    motion_error_cart::In_P_motion_error_cart motion_error_0_p;
    this->_motion_error_0.initialize(this->_motion_error_0_u,motion_error_0_p);

    //    this->_wave_variables.p.master<<c->master;
    //    this->_wave_variables.p.b<<0,0,0,0,0,0;
    //    this->_wave_variables.p.lambda_u_l<<0,0,0,0,0,0;
    //    this->_wave_variables.p.lambda_u_r<<0,0,0,0,0,0;
    //    this->_wave_variables.u.dX_l<<0,0,0,0,0,0;
    //    this->_wave_variables.u.F_r<<0,0,0,0,0,0;
    //    this->_wave_variables.u.v_l<<0,0,0,0,0,0;
    //    this->_wave_variables.u.v_r<<0,0,0,0,0,0;
    //    this->_wave_variables.initialize();
}

CmdMP& mp_telepresence::step(const Percept &p){
    std::shared_ptr<ConfigMP_mp_telepresence> c = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->_config);
    std::vector<double> payload;
    if(c->mode==TelepresenceMode::Joystick){
        this->joystick_mode(p,payload);
    }
    this->msg_out(payload);
    return this->_cmd;
}

void mp_telepresence::terminate(){
    std::shared_ptr<ConfigMP_mp_telepresence> c = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->_config);
    this->_motion_error.terminate();
    this->_motion_error_0.terminate();
    int r=close(this->_s_out);
    if(r<0){
        msrm_utils::print_error("Socket could not be closed successfully.");
    }
    if(c->repeater){
        r=close(this->_s_rep);
        if(r<0){
            msrm_utils::print_error("Socket could not be closed successfully.");
        }
    }
    this->_thread_should_run=false;
}

bool mp_telepresence::check_attractor(){
    return true;
}

bool mp_telepresence::init_attractor(const Percept &p, const std::shared_ptr<ConfigUser> config){
    return true;
}

bool mp_telepresence::in_attractor(const Percept &p){
    return true;
}

void mp_telepresence::setup_logs(unsigned long long length){

}

void mp_telepresence::write_logs(){

}

bool mp_telepresence::initialize_connections(){
    std::shared_ptr<ConfigMP_mp_telepresence> config = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->_config);
    // Initialize member variables
    this->_flag_connected=false;
    this->_flag_valid_package=false;
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

    msrm_utils::print_info("Outgoing connection configured with url "+ip_dst+":"+std::to_string(config->port_dst));

    if(config->repeater){
        this->_slen_rep=sizeof(this->_si_other_rep);
        if ((this->_s_rep=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
        {
            msrm_utils::print_error("Initialization of repeater connection failed.");
            return false;
        }
        memset((char *) &this->_si_other_rep, 0, sizeof(this->_si_other_rep));
        this->_si_other_rep.sin_family = AF_INET;
        this->_si_other_rep.sin_port = htons(config->port_dst);
        inet_aton(config->ip_dst.c_str(), &this->_si_other_rep.sin_addr);
    }

    // Incoming connection
    this->_slen_in = sizeof(this->_si_other_in);
    if((this->_s_in=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1){ // If socket for incoming connection could not be created...
        msrm_utils::print_error("Initialization of incoming connection failed.");
        return false;
    }

    // Set timeout of 10 ms for incoming UDP connection for direct modes
    if(config->mode==TelepresenceMode::JointDirect || config->mode==TelepresenceMode::CartesianDirect){
        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 10000;
        setsockopt(this->_s_in, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);
    }
    if(config->mode==TelepresenceMode::Joystick){
        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 10000;
        setsockopt(this->_s_in, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);
    }

    memset((char *) &this->_si_me_in, 0, sizeof(this->_si_me_in));
    this->_si_me_in.sin_family = AF_INET;
    this->_si_me_in.sin_port = htons(config->port_recv);
    this->_si_me_in.sin_addr.s_addr=htonl (INADDR_ANY);
    bind(this->_s_in , (struct sockaddr*)&this->_si_me_in, sizeof(this->_si_me_in));

    if(config->ip_dst=="225.0.0.1" && !config->repeater && !config->master){
        struct ip_mreq mreq;

        mreq.imr_multiaddr.s_addr = inet_addr("225.0.0.1");
        mreq.imr_interface.s_addr = htonl(INADDR_ANY);
        int err=setsockopt(this->_s_in,IPPROTO_IP,IP_ADD_MEMBERSHIP,&mreq,sizeof(mreq));
        if(err<0){
            msrm_utils::print_critical_error("Can not set socket options for multicast.");
            this->set_flag_error();
        }
    }

    if(config->bilateral || !config->master){
        this->_thread_should_run=true;
        this->_thr_msg_in=std::thread(&mp_telepresence::msg_in,this);
        this->_thr_msg_in.detach();
    }

    // Incoming connection was properly created.

    msrm_utils::print_info("Incoming connection configured with port: "+std::to_string(config->port_recv));

    return true;
}

void mp_telepresence::joystick_mode(const Percept &p, std::vector<double> &payload){
    std::shared_ptr<ConfigMP_mp_telepresence> c = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->_config);

    if(c->master){ // if this prototype is the master...

        // Parameter that determines control mode (translation or rotation) is read from live parameter server.
        nlohmann::json param=this->_kb->get_live_parameter("joystick_translation_on");
        if(!param.is_null()){
            param.get_to(this->_flag_joystick_translation);
        }
        param=this->_kb->get_live_parameter("joystick_rotation_on");
        if(!param.is_null()){
            param.get_to(this->_flag_joystick_rotation);
        }
        Eigen::Matrix<double,6,1> EE_F_ext=Eigen::Matrix<double,6,1>(this->_EE_F_ext_in[0].data());

        if(this->_flag_joystick_translation){ // if control mode is rotation mode...
            this->_cmd.K_x(0)=c->K_joystick_on(0);
            this->_cmd.K_x(1)=c->K_joystick_on(2);
            this->_cmd.K_x(2)=c->K_joystick_on(2);
        }else{ // if control mode is translation mode...
            this->_cmd.K_x(0)=c->K_joystick_off(0);
            this->_cmd.K_x(1)=c->K_joystick_off(2);
            this->_cmd.K_x(2)=c->K_joystick_off(2);
        }
        if(this->_flag_joystick_rotation){ // if control mode is rotation mode...
            this->_cmd.K_x(3)=c->K_joystick_on(3);
            this->_cmd.K_x(4)=c->K_joystick_on(4);
            this->_cmd.K_x(5)=c->K_joystick_on(5);
        }else{ // if control mode is translation mode...
            this->_cmd.K_x(3)=c->K_joystick_off(3);
            this->_cmd.K_x(4)=c->K_joystick_off(4);
            this->_cmd.K_x(5)=c->K_joystick_off(5);
        }

        // Bring external forces from slave to torques at master
        EE_F_ext(3)=EE_F_ext(4)=EE_F_ext(5)=0; // Set moments to zero (hard to handle in Cartesian telepresence settings)
        Eigen::Matrix<double,3,1> moments = EE_F_ext.block<3,1>(0,0).cross(c->joystick_lever);
        EE_F_ext(3)=moments(0);
        EE_F_ext(4)=moments(1);
        EE_F_ext(5)=moments(2);
        Eigen::Matrix<double,7,1> tau_ext=p.B_J_EE.transpose()*2*EE_F_ext; // Transform from wrench at J frame to torques

        // Write external torques coming from slave to command struct
        for(unsigned i=0;i<7;i++){
            this->_cmd.tau_ff(i)=tau_ext(i);
        }

        // Write input of Cartesian error calculator
        this->_motion_error_u.O_T_EE=Eigen::Matrix<double,4,4>(p.TF_T_EE);
        this->_motion_error_u.O_T_EE_d=Eigen::Matrix<double,4,4>(p.TF_T_EE_d);
        this->_motion_error.step(this->_motion_error_u,this->_motion_error_y);

        Eigen::Matrix<double,6,1> O_diff;
        if(!c->joystick_force_input){
            O_diff = -this->_motion_error_y.e;
        }else{
            O_diff = -p.O_F_ext;
        }
        Eigen::Matrix<double,6,1> EE_dX_d;

        Eigen::Matrix<double,6,1> EE_diff=msrm_utils::rotate_vector(O_diff,msrm_utils::invert_transformation_matrix(p.TF_T_EE)); // Transform into EE frame
        EE_diff(3)=EE_diff(0);
        EE_diff(4)=EE_diff(1);
        EE_diff(5)=EE_diff(2);
        for(unsigned i=0;i<6;i++){
            if(fabs(EE_diff(i))<c->joystick_deadband(i)){ // If the difference is smaller than the deadzone...
                EE_dX_d(i)=0; // Set velocity to zero in direction i
            }else{ // If the difference is larger than the deadzone...
                EE_dX_d(i)=(fabs(EE_diff(i))-c->joystick_deadband(i))*c->joystick_amp(i); // Subtract deadzone from difference
                EE_dX_d(i)*=msrm_utils::sgn(EE_diff(i)); // Apply sign
            }
            if(!this->_flag_joystick_translation && i<3){
                EE_dX_d(i)=0;
            }
            if(!this->_flag_joystick_rotation && i>2){
                EE_dX_d(i)=0;
            }
        }

        for(unsigned i=0;i<6;i++){
            payload.push_back(EE_dX_d(i)); // Push commands into payload.
        }
    }else{ // if this prototype is the slave

        nlohmann::json param=this->_kb->get_live_parameter("joystick_selector");
        if(!param.is_null()){
            msrm_utils::read_json_param<bool,6,1>(param,this->_joystick_selector);
        }

        this->_motion_error_0_u.O_T_EE=Eigen::Matrix<double,4,4>(p.TF_T_EE);
        this->_motion_error_0_u.O_T_EE_d=Eigen::Matrix<double,4,4>(c->joystick_funnel_pose);
        this->_motion_error_0.step(this->_motion_error_0_u,this->_motion_error_0_y);

        Eigen::Matrix<double,3,3> EE_T_J_t,EE_T_J_r;
        param=this->_kb->get_live_parameter("EE_T_J_t");
        if(!param.is_null()){
            msrm_utils::read_json_param<double,3,3>(param,EE_T_J_t);
            if(!msrm_utils::is_orthonormal(EE_T_J_t)){
                EE_T_J_t=c->EE_T_J_t;
            }
        }else{
            EE_T_J_t=c->EE_T_J_t;
        }
        param=this->_kb->get_live_parameter("EE_T_J_r");
        if(!param.is_null()){
            msrm_utils::read_json_param<double,3,3>(param,EE_T_J_r);
            //            if(!msrm_utils::is_orthonormal(EE_T_J_r)){
            //                EE_T_J_r=c->EE_T_J_r;
            //            }
        }else{
            EE_T_J_r=c->EE_T_J_r;
        }

        param=this->_kb->get_live_parameter("dX_max");
        Eigen::Matrix<double,2,1> dX_max;
        if(!param.is_null()){
            msrm_utils::read_json_param<double,2,1>(param,dX_max);
            this->_joystick_dX_max<<dX_max(0),dX_max(0),dX_max(0),dX_max(1),dX_max(1),dX_max(1);
        }

        Eigen::Matrix<double,4,4> O_T_EE=Eigen::Matrix<double,4,4>(p.O_T_EE);
        Eigen::Matrix<double,6,1> J_dX_d=Eigen::Matrix<double,6,1>(this->_O_dX_d_in[0].data());
        Eigen::Matrix<double,6,1> EE_e=msrm_utils::rotate_vector(this->_motion_error_0_y.e,msrm_utils::invert_transformation_matrix(O_T_EE));
        Eigen::Matrix<double,3,1> J_e=EE_T_J_r.transpose()*EE_e.block<3,1>(3,0);
        for(unsigned i=0;i<3;i++){
            if(J_e(i)<=this->_rot_limits(2*i) && J_dX_d(i+3)>0){
                J_dX_d(i+3)=0;
            }
            if(J_e(i)>=this->_rot_limits(2*i+1) && J_dX_d(i+3)<0){
                J_dX_d(i+3)=0;
            }
        }

        // STEPWISE CONSTRAINT
        if(c->joystick_stepwise){
            for(unsigned i=0;i<3;i++){
                if(fabs(J_dX_d(i))==0){
                    this->_J_dX_step(i)=0;
                }else{
                    this->_J_dX_step(i)+=J_dX_d(i)*0.001;
                }
                if(fabs(this->_J_dX_step(i))>c->joystick_step_size(0)){
                    J_dX_d.setZero();
                }
                if(fabs(J_dX_d(i+3))==0){
                    this->_J_dX_step(i+3)=0;
                }else{
                    this->_J_dX_step(i+3)+=J_dX_d(i+3)*0.001;
                }
                if(fabs(this->_J_dX_step(i+3))>c->joystick_step_size(1)){
                    J_dX_d.setZero();
                }
            }
        }
        for(unsigned i=0;i<6;i++){
            if(J_dX_d(i)>this->_joystick_dX_max(i))J_dX_d(i)=this->_joystick_dX_max(i); // If velocity command is larger than maximum allowed velocity, cap it.
            if(J_dX_d(i)<-this->_joystick_dX_max(i))J_dX_d(i)=-this->_joystick_dX_max(i); // If velocity command is smaller than maximum allowed negative velocity, cap it.
        }

        Eigen::Matrix<double,3,1> EE_dX_t_d, EE_dX_r_d;
        Eigen::Matrix<double,6,1> EE_dX_d;
        EE_dX_t_d=EE_T_J_t*J_dX_d.block<3,1>(0,0);
        EE_dX_r_d=EE_T_J_r*J_dX_d.block<3,1>(3,0);
        EE_dX_d<<EE_dX_t_d,EE_dX_r_d;

        for(unsigned i=0;i<6;i++){
            if(!this->_joystick_selector(i)){
                EE_dX_d(i)=0;
            }
        }
        double F_thr=5;
        double sigma;
        Eigen::Matrix<double,6,1> F_e=-p.K_F_ext;
        for(unsigned i=0;i<6;i++){
            if(abs(F_e(i))>F_thr && F_e(i)*EE_dX_d(i) < 0){
                sigma = exp(F_thr-abs(F_e(i)));
            }else{
                sigma=1;
            }
            if(sigma>1)sigma=1;
            if(sigma<0)sigma=0;
            EE_dX_d(i)*=sigma;
        }

        Eigen::Matrix<double,6,1> O_dX_d=msrm_utils::rotate_vector(EE_dX_d,O_T_EE); // Transform incoming velocity form master into O frame
        Eigen::Matrix<double,3,1> J_F_ext_t=EE_T_J_t.transpose()*p.K_F_ext.block<3,1>(0,0);
        Eigen::Matrix<double,3,1> J_F_ext_r=EE_T_J_r.transpose()*p.K_F_ext.block<3,1>(3,0);
        Eigen::Matrix<double,6,1> J_F_ext;
        J_F_ext<<-J_F_ext_t,-J_F_ext_r;

        this->_cmd.TF_dX_d=O_dX_d;
        // Push external wrench into payload
        for(unsigned i=0;i<6;i++){
            payload.push_back(J_F_ext(i));
        }
    }
}

void mp_telepresence::joint_direct_mode(const Percept &p, std::vector<double> &payload){
    std::shared_ptr<ConfigMP_mp_telepresence> c = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->_config);
    Eigen::Matrix<double,7,1> q = Eigen::Matrix<double,7,1>(this->_q_d_in[0].data());
    Eigen::Matrix<double,7,1> dq = Eigen::Matrix<double,7,1>(this->_dq_d_in[0].data());
    Eigen::Matrix<double,7,1> tau_ext = Eigen::Matrix<double,7,1>(this->_tau_ext_in[0].data());
    if(c->master){
        for(unsigned i=0;i<7;i++){
            this->_cmd.tau_d(i)-=tau_ext[i];
            double dq=p.dq[i];
            double P_s=dq*tau_ext[i];
            double p_thr=3;
            double power_scale;
            power_scale=1-0.5*(1-cos(M_PI*(1-P_s/p_thr)));
            if(P_s>p_thr)power_scale=0;
            if(P_s<=0)power_scale=1;

            this->_cmd.tau_ff(i)-=power_scale*c->joint_direct_alpha(i)*msrm_utils::sgn(dq)*fabs(P_s);
        }
    }else{
        for(unsigned i=0;i<7;i++){
            //            if(c->enable_ffwd_tau){
            //                this->_cmd.tau_ff(i)-=tau_ext[i];
            //            }
        }
        this->_cmd.q_d=q;
    }
}

bool mp_telepresence::msg_out(const std::vector<double> &payload){
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

void mp_telepresence::msg_in() {

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
        if(!this->_thread_should_run){ // If an interrupt exception occurs...
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
                msrm_utils::print_critical_error("Lost 200 packets in a row. I assume the network connection is faulty and will terminate.");
                msg_connection_lost=true;
            }
            this->write_safe_message();
//            this->set_flag_error(); // Terminate prototype
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
            payload.push_back(q_union.f); // Converted data element is pushed into the payload vector
        }
        // Unload the payload. This function has to be defined by the respective telepresence prototype.
        this->unload_msg(payload);
    }
}

bool mp_telepresence::unload_msg(const std::vector<double> &payload){
    std::shared_ptr<ConfigMP_mp_telepresence> c = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->_config);
    if(c->mode==TelepresenceMode::Joystick){
        if(c->master){ // If this prototype is master...
            if(payload.size()!=6){ // If payload does not have 6 elements...
                msrm_utils::print_error("Size of payload is "+std::to_string(payload.size())+" but expected is 6.");
                return false;
            }
            // Read payload into thread-safe container
            for(unsigned i=0;i<6;i++){
                this->_EE_F_ext_in[0][i]=payload[i];
            }
        }else{ // If this prototype is slave...
            if(payload.size()!=6){ // If payload does not have 6 elements...
                msrm_utils::print_error("Size of payload is "+std::to_string(payload.size())+" but expected is 6.");
                return false;
            }
            // Read payload into thread-safe container
            for(unsigned i=0;i<6;i++){
                this->_O_dX_d_in[0][i]=payload[i];
            }
        }
    }
    return false;
}

void mp_telepresence::write_safe_message(){
    std::shared_ptr<ConfigMP_mp_telepresence> c = std::static_pointer_cast<ConfigMP_mp_telepresence>(this->_config);
    if(c->mode==TelepresenceMode::Joystick){
        if(c->master){ // If this prototype is master...
            // Read payload into thread-safe container
            for(unsigned i=0;i<6;i++){
                this->_EE_F_ext_in[0][i]=0;
            }
        }else{ // If this prototype is slave...
            // Read payload into thread-safe container
            for(unsigned i=0;i<6;i++){
                this->_O_dX_d_in[0][i]=0;
            }
        }
    }
}

}

