#include "tasks/telepresence.hpp"

namespace mios {

telepresence::telepresence():Task("telepresence"){
}
void telepresence::initialize_task(){
    this->create_skill<telepresence_master>("master");
    this->create_skill<telepresence_slave>("slave");

    this->create_subtask<move_to_joint_pose>("move_joint");
    this->create_subtask<move_to_cart_pose>("move_cart");

}
void telepresence::execute_task(){

    if(this->_master){
        std::static_pointer_cast<ConfigSkill_telepresence_master>(this->get_skill("master")->get_config())->bilateral=this->_bilateral;
        std::static_pointer_cast<ConfigSkill_telepresence_master>(this->get_skill("master")->get_config())->mode=this->_mode;
        if(this->_mode==TelepresenceMode::JointDirect){
            this->get_skill("master")->get_config()->controller.K_theta<<0,0,0,0,0,0,0;
            this->get_skill("master")->get_config()->controller.xi_theta<<0,0,0,0,0,0,0;
            this->get_skill("master")->get_config()->general.control_mode=2;
        }
        if(this->_mode==TelepresenceMode::CartesianDirect){
            //            static_cast<Config_telepresence_master*>(this->get_skill("master")->get_config())->controller.K_0<<1000,1000,1000,10,10,10;
            this->get_skill("master")->get_config()->controller.K_0<<0,0,0,0,0,0;
            this->get_skill("master")->get_config()->controller.xi<<0.7,0.7,0.7,0.7,0.7,0.7;
            this->get_skill("master")->get_config()->general.control_mode=0;
        }
        if(this->_mode==TelepresenceMode::Joystick){
            this->get_skill("master")->get_config()->general.control_mode=0;
        }
        if(this->_alias_peer=="225.0.0.1"){
            std::static_pointer_cast<ConfigSkill_telepresence_master>(this->get_skill("master")->get_config())->ip_dst=this->_alias_peer;
        }else{
            std::string ip_peer;
            ip_peer=msrm_utils::get_ip_by_hostname(this->_alias_peer.c_str()).value_or("");
            if(ip_peer==""){
                msrm_utils::print_error("Could not acquire peer IP from host " +this->_alias_peer+" .");
                return;
            }else{
                msrm_utils::print_info("Peer IP is "+ip_peer+".");
            }
            std::static_pointer_cast<ConfigSkill_telepresence_master>(this->get_skill("master")->get_config())->ip_dst=ip_peer;
        }
        //        while(!this->get_stop_flag()){
        //            if(this->_alias_peer[0]!="225.0.0.1" && this->_bilateral){
        //                nlohmann::json response;
        //                nlohmann::json request;
        //                for(unsigned i=0;i<10;i++){
        //                    if(!msrm_utils::rpc_call("http://"+ip_peer+":8383","get_state",request,response,1000)){
        //                        std::cout<<"FAIL"<<std::endl;
        //                        sleep(1);
        //                        continue;
        //                    }
        //                    Eigen::Matrix<double,7,1> q_master,q_slave;
        //                    const Percept p = this->request_percept();
        //                    q_master=p.q;
        //                    msrm_utils::read_json_param<double,7,1>(response["q"],q_slave);
        //                    bool synced=true;
        //                    for(unsigned j=0;j<7;j++){
        //                        if(fabs(q_master(j)-q_slave(j))>this->get_skill("master")->get_config()->user.e_q_max(0)){
        //                            synced=false;
        //                        }
        //                        if(fabs(p.tau_ext(j))>this->get_skill("master")->get_config()->user.tau_contact(j)){
        //                            msrm_utils::print_error("Please do not push the master during syncing.");
        //                            return;
        //                        }
        //                    }
        //                    if(synced){
        //                        break;
        //                    }
        //                    if(i==9){
        //                        msrm_utils::print_error("Could not sync with slave. Angle discrepancies are too large.");
        //                        return;
        //                    }
        //                    sleep(1);
        //                }
        //            }
        this->load_led_pattern(std::shared_ptr<pattern_white>(new pattern_white()));
        this->execute_skill("master");
        //        }
    }else{
        nlohmann::json settings;
        nlohmann::json parameters;
        if(this->_mode==TelepresenceMode::JointDirect){
            msrm_utils::write_json_array<double,7,1>(parameters["q_g"],this->_q_0);
            settings["parameters"]=parameters;
            this->get_subtask("move_joint")->read_parameters(parameters);
            this->execute_subtask("move_joint");
            if(!this->get_subtask("move_joint")->get_eval().success){
                msrm_utils::print_error("Could not move to synchronization pose, aborting telepresence.");
                return;
            }
        }
        if(this->_mode==TelepresenceMode::CartesianDirect){
//            Eigen::Matrix<double,4,4> O_T_W=msrm_utils::invert_transformation_matrix(std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->get_skill("slave")->get_config())->W_T_O);
//            msrm_utils::write_json_array<double,4,4>(parameters["TF_T_EE_g"],msrm_utils::rotate_matrix(this->_TF_T_EE_0,O_T_W));
            parameters["speed"]=1;
            parameters["acc"]=0.5;
            settings["parameters"]=parameters;
            this->get_subtask("move_cart")->read_parameters(parameters);
            this->execute_subtask("move_cart");
            if(!this->get_subtask("move_cart")->get_eval().success){
                msrm_utils::print_error("Could not move to synchronization pose, aborting telepresence.");
                return;
            }
        }
        if(this->_mode==TelepresenceMode::Joystick){
        }

        std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->get_skill("slave")->get_config())->bilateral=this->_bilateral;
        std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->get_skill("slave")->get_config())->mode=this->_mode;
        if(this->_mode==TelepresenceMode::JointDirect){
            this->get_skill("slave")->get_config()->general.control_mode=2;
        }
        if(this->_mode==TelepresenceMode::CartesianDirect){
            this->get_skill("slave")->get_config()->general.control_mode=0;
        }
        if(this->_mode==TelepresenceMode::Joystick){
            this->get_skill("slave")->get_config()->general.control_mode=0;
        }

        if(this->_repeater){
            std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->get_skill("slave")->get_config())->ip_dst="225.0.0.1";
            std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->get_skill("slave")->get_config())->repeater=true;
        }else{
            if(this->_alias_peer=="225.0.0.1"){
                std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->get_skill("slave")->get_config())->ip_dst=this->_alias_peer;
            }else{
                std::string ip_peer=msrm_utils::get_ip_by_hostname(this->_alias_peer.c_str()).value_or("");
                if(ip_peer==""){
                    msrm_utils::print_error("Could not acquire peer IP from host " +this->_alias_peer+".");
                    return;
                }else{
                    msrm_utils::print_info("Peer IP is "+ip_peer+".");
                }
                std::static_pointer_cast<ConfigSkill_telepresence_slave>(this->get_skill("slave")->get_config())->ip_dst=ip_peer;
            }
        }
        this->load_led_pattern(std::shared_ptr<pattern_white>(new pattern_white()));
        this->execute_skill("slave");
    }
}
const EvalTask& telepresence::evaluate_task(){
    this->_eval_task.cost_suc=0;
    this->_eval_task.cost_err=0;
    this->_eval_task.success=true;
    return this->_eval_task;
}

bool telepresence::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"master",this->_master)){
        msrm_utils::print_error("Missing parameter: master");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"repeater",this->_repeater)){
        this->_repeater=false;
    }
    if(this->_repeater && this->_master){
        msrm_utils::print_error("Can not be master and repeater at the same time.");
        return false;
    }
    std::string mode;
    if(!msrm_utils::read_json_param(params,"mode",mode)){
        mode="none";
    }
    this->_mode=TelepresenceMode::None;
    if(mode=="joystick"){
        this->_mode=TelepresenceMode::Joystick;
    }
    if(!msrm_utils::read_json_param<double,7,1>(params,"q_0",this->_q_0) && !this->_master && this->_mode==TelepresenceMode::JointDirect){
        msrm_utils::print_error("Missing parameter: q_0 [7x1] - Initial joint pose, should coincide with the master.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,4,4>(params,"TF_T_EE_0",this->_TF_T_EE_0) && !this->_master && this->_mode==TelepresenceMode::CartesianDirect){
        msrm_utils::print_error("Missing parameter: TF_T_EE_0 [4x4] - Initial Cartesian pose, should coincide with the master.");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"alias_peer",this->_alias_peer) && !this->_repeater){
        msrm_utils::print_error("Missing parameter: alias_peer.");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"bilateral",this->_bilateral)){
        this->_bilateral=true;
    }

    return true;
}

}
