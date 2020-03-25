#include "collective_module/collective_module.hpp"

#include "knowledge_base/knowledge_base.hpp"
#include "cpp_utils/network.hpp"
#include "cpp_utils/files.hpp"

namespace mios {

CollectiveModule::CollectiveModule(){
    this->_flag_primary=true;
    this->_flag_hear_primary=false;
    this->_len_msg=23;
    this->_cnt_silence=0;
    this->_current_primary="none";
    this->set_as_primary();
}

CollectiveModule::~CollectiveModule(){

}

void CollectiveModule::cycle(){
//    while(true){
//        if(!this->_flag_primary){
//            this->_cnt_silence++;
//        }else{
//            this->_cnt_silence=0;
//        }
//        if(this->_cnt_silence>=3){
//            this->_cnt_silence=0;
//            cpp_utils::print_warning("I lost contact to primary, reorganizing.");
//            this->set_as_primary();
//        }
//        if(!this->_thr_listen.joinable()){
//            cpp_utils::print_info("Starting to listen for primaries.");
//            this->_thr_listen=boost::thread(&CollectiveModule::listen,this);
//        }
//        assert(!(!this->_flag_primary && this->_current_primary=="none"));
//        if(this->_flag_primary){
//            this->_mtx_queue.lock();
//            while(this->_queue_primaries.size()!=0){
//                if(!this->_flag_primary){
//                    break;
//                }
//                this->lock_negotiations();
//                std::string ip=*this->_queue_primaries.begin();
//                nlohmann::json req_negotiation,res_negotiation;
//                req_negotiation["ip"]=cpp_utils::get_own_ip("tap0");
//                bool won;
//                cpp_utils::print_info("Negotiating with "+ip+".");
//                if(!cpp_utils::rpc_call("http://"+ip+":8383","negotiate_primary",req_negotiation,res_negotiation)){
//                    won=true;
//                }else if(!cpp_utils::read_json_param(res_negotiation["won"],won)){
//                    won=true;
//                }
//                if(!won){
//                    nlohmann::json request,response;
//                    for(std::pair<std::string,Robot*> r : this->_robots){
//                        request["robots"].append(r.second->to_json());
//                    }
//                    if(!cpp_utils::rpc_call("http://"+ip+":8383","copy_server_info",request,response)){
//                        this->_queue_primaries.pop_front();
//                        cpp_utils::print_info("I remain primary.");
//                    }else{
//                        this->_queue_primaries.clear();
//                        this->set_as_secondary(ip);
//                        cpp_utils::print_info("I am secondary now, my primary is "+ip+".");
//                    }
//                }else{
//                    cpp_utils::print_info("I remain primary.");
//                    std::string ip_next;
//                    if(cpp_utils::read_json_param(res_negotiation["ip_primary"],ip_next)){
//                        if(ip_next!="none" && ip_next!=cpp_utils::get_own_ip("tap0")){
//                            this->_queue_primaries.clear();
//                            this->_queue_primaries.push_back(ip_next);
//                        }else{
//                            this->_queue_primaries.pop_front();
//                        }
//                    }
//                    nlohmann::json request,response;
//                    if(!cpp_utils::rpc_call("http://"+ip+":8383","get_identity",request,response)){

//                    }else{
//                        std::string id;
//                        cpp_utils::read_json_param(response["id"],id);
//                        Robot r(id);
//                        r.set_ip(ip);
//                        this->add_robot(r);
//                    }
//                }
//                this->unlock_negotiations();
//            }
//            this->_mtx_queue.unlock();
//        }
//        sleep(1);
//    }
}

bool CollectiveModule::broadcast(){
//    struct sockaddr_in broadcastAddr;
//    std::string ip=cpp_utils::get_own_ip("tap0");
//    std::vector<std::string> ip_parts=cpp_utils::split_string(ip,".");
//    std::string ip_broadcast = ip_parts[0]+"."+ip_parts[1]+"."+ip_parts[2]+".255";
//    unsigned port_broadcast = 8391;
//    char msg[this->_len_msg];
//    unsigned cnt_msg=0;
//    msg[cnt_msg++]=127;
//    msg[cnt_msg++]=127;
//    msg[cnt_msg++]=127;
//    msg[cnt_msg++]=127;
//    ip=cpp_utils::convert_ip_to_default_format(ip);
//    for(unsigned i=0;i<ip.size();i++){
//        msg[cnt_msg++]=ip[i];
//    }
//    msg[cnt_msg++]=126;
//    msg[cnt_msg++]=126;
//    msg[cnt_msg++]=126;
//    msg[cnt_msg++]=126;

//    int s;
//    if((s = socket(AF_INET,SOCK_DGRAM,0))<0){
//        cpp_utils::print_error("Could not create socket for primary broadcast.");
//        return false;
//    }

//    int broadcastEnable=1;
//    int ret=setsockopt(s, SOL_SOCKET, SO_BROADCAST, &broadcastEnable, sizeof(broadcastEnable));
//    if(ret<0){
//        std::cout<<std::strerror(errno)<<std::endl;
//        cpp_utils::print_info("Could not set options for primary broadcast.");
//        return false;
//    }

//    memset(&broadcastAddr, 0, sizeof(broadcastAddr));
//    broadcastAddr.sin_family = AF_INET;
//    broadcastAddr.sin_addr.s_addr = inet_addr(ip_broadcast.c_str());
//    broadcastAddr.sin_port = htons(port_broadcast);

//    try{
//        while(true){
//            cpp_utils::print_info("Broadcasting...");
//            if (sendto(s, msg, strlen(msg), 0, (struct sockaddr *)&broadcastAddr, sizeof(broadcastAddr)) != strlen(msg)){
//                cpp_utils::print_error("Error when sending primary broadcast.");
//                return false;
//            }
//            boost::this_thread::sleep_for(boost::chrono::milliseconds(100));
//        }
//    }catch(boost::thread_interrupted const&){
//        close(s);
//        this->_thr_broadcast.detach();
//        return true;
//    }
//    return true;
}

bool CollectiveModule::listen(){
    int s;
    struct sockaddr_in broadcastAddr;
    unsigned port_broadcast=8391;
    char recvString[255];
    int recvStringLen;

    if ((s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0){
        cpp_utils::print_error("Could not create socket for listener thread.");
        return false;
    }
    struct timeval tv;
    tv.tv_sec = 0.5;
    tv.tv_usec = 0;
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);

    memset(&broadcastAddr, 0, sizeof(broadcastAddr));
    broadcastAddr.sin_family = AF_INET;
    broadcastAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    broadcastAddr.sin_port = htons(port_broadcast);

    if (bind(s, (struct sockaddr *) &broadcastAddr, sizeof(broadcastAddr)) < 0){
        cpp_utils::print_error("Binding of socket in listener thread failed.");
        return false;
    }

    try{
        while(true){
            boost::this_thread::sleep_for(boost::chrono::milliseconds(100));
            if ((recvStringLen = recvfrom(s, recvString, 255, 0, NULL, 0)) < 0){
                //                cpp_utils::print_error("I do not hear any primaries.");
            }else{
                unsigned i=0;
                for(;i<255-this->_len_msg+1;i++){
                    if(recvString[i]==127 && recvString[i+1]==127 && recvString[i+2]==127 && recvString[i+3]==127 &&
                            recvString[i+this->_len_msg-4]==126 && recvString[i+this->_len_msg-3]==126 && recvString[i+this->_len_msg-2]==126 && recvString[i+this->_len_msg-1]==126){
                        break;
                    }
                }
                if(i<255-this->_len_msg+1){
                    std::string msg=std::string(recvString);
                    std::string ip = cpp_utils::convert_ip_from_default_format(std::string(msg.begin()+4, msg.begin() + 19));
                    if(ip==cpp_utils::get_own_ip("tap0")){
                        continue;
                    }
                    bool is_in_queue=false;
                    this->_mtx_queue.lock();
                    for(std::list<std::string>::iterator itr=this->_queue_primaries.begin();itr!=this->_queue_primaries.end();++itr){
                        if(*itr==ip){
                            is_in_queue=true;
                        }
                    }
                    if(ip==this->_current_primary){
                        this->_cnt_silence=0;
                    }
                    if(ip!=cpp_utils::get_own_ip("tap0") && !is_in_queue && this->_flag_primary){
                        cpp_utils::print_info("I hear a primary with ip "+ip+".");
                        this->_queue_primaries.push_back(ip);
                    }
                    this->_mtx_queue.unlock();
                }
            }

        }
    }catch(boost::thread_interrupted const&){
        close(s);
        return true;
    }

    return true;
}

void CollectiveModule::set_as_primary(){
    this->_flag_primary=true;
    this->_current_primary="none";
//    cpp_utils::print_info("Starting broadcast.");
//    this->_thr_broadcast=boost::thread(&CollectiveModule::broadcast,this);
}

void CollectiveModule::set_as_secondary(std::string ip_primary){
//    this->_current_primary=ip_primary;
//    this->_flag_primary=false;
//    cpp_utils::print_info("Terminating broadcast.");
//    this->_thr_broadcast.interrupt();
}

std::map<std::string,Robot*>* CollectiveModule::get_robots(){
    return &this->_robots;
}

std::string CollectiveModule::get_primary_ip(){
    return this->_current_primary;
}

bool CollectiveModule::add_robot(Robot r){
    if(this->has_robot(r.get_id())){
        cpp_utils::print_warning("Robot "+r.get_id()+" is already in collective");
        return false;
    }
    if(this->_black_list_robots.find(r.get_id())!=this->_black_list_robots.end()){
        cpp_utils::print_error("Robot "+r.get_hostname()+" is blacklisted. Can not add to collective.");
        return false;
    }
    Robot* robot = new Robot(r.get_id());
    this->_robots.insert(std::pair<std::string,Robot*>(r.get_id(),robot));
    return true;
}

bool CollectiveModule::remove_robot(std::string robot){
    if(!this->has_robot(robot)){
        cpp_utils::print_warning("Collective has no member "+robot+".");
        return false;
    }
    std::map<std::string,Robot*>::iterator it=this->_robots.find(robot);
    this->_robots.erase(it);
    return true;
}

bool CollectiveModule::whitelist_robot(std::string robot){
    std::set<std::string>::iterator it=this->_black_list_robots.find(robot);
    if(it==this->_black_list_robots.end()){
        cpp_utils::print_warning("Robot "+robot+" is not on black list.");
        return false;
    }
    this->_black_list_robots.erase(it);
    return true;
}

bool CollectiveModule::blacklist_robot(std::string robot){
    std::set<std::string>::iterator it=this->_black_list_robots.find(robot);
    if(it!=this->_black_list_robots.end()){
        cpp_utils::print_warning("Robot "+robot+" is already blacklisted.");
        return false;
    }
    std::map<std::string,Robot*>::iterator it_robot=this->_robots.find(robot);
    if(this->has_robot(robot)){
        cpp_utils::print_warning("Robot "+robot+" has been blacklisted and will be removed from the collectiev.");
        this->_robots.erase(it_robot);
    }
    this->_black_list_robots.insert(robot);
    return true;
}

bool CollectiveModule::is_primary(){
    return this->_flag_primary;
}

void CollectiveModule::lock_negotiations(){
    this->_mtx_negotiations.lock();
}

void CollectiveModule::unlock_negotiations(){
    this->_mtx_negotiations.unlock();
}

bool CollectiveModule::has_robot(std::string robot){
    return this->_robots.find(robot)!=this->_robots.end();
}

}
