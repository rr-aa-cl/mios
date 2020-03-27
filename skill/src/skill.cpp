#include "skill/skill.hpp"
#include <franka/exception.h>
#include <chrono>

#include "cpp_utils/math.hpp"

namespace mios {

CmdSkill::CmdSkill(){
    this->reset();
}

void CmdSkill::read_mp_cmd(const CmdMP &cmd){
    this->TF_T_EE_d=cmd.TF_T_EE_d;
    this->TF_dX_d=cmd.TF_dX_d;
    this->TF_F_d=cmd.TF_F_d;
    this->TF_F_ff=cmd.TF_F_ff;
    this->K_x=cmd.K_x;
    this->xi_x=cmd.xi_x;

    this->q_d=cmd.q_d;
    this->dq_d=cmd.dq_d;
    this->tau_d=cmd.tau_d;
    this->tau_ff=cmd.tau_ff;
    this->K_theta=cmd.K_theta;
    this->xi_theta=cmd.xi_theta;

    this->TF_T_EE_d_buffer=this->TF_T_EE_d;
    this->TF_dX_d_buffer=this->TF_dX_d;
    this->TF_F_ff_buffer=this->TF_F_ff;
    this->TF_F_d_buffer=this->TF_F_d;
    this->K_x_buffer=this->K_x;
    this->xi_x_buffer=this->xi_x;

    this->q_d_buffer=this->q_d;
    this->dq_d_buffer=this->dq_d;
    this->tau_d_buffer=this->tau_d;
    this->tau_ff_buffer=this->tau_ff;
    this->K_theta_buffer=this->K_theta;
    this->xi_theta_buffer=this->xi_theta;

    this->on_cntrl_imp=cmd.on_cntr_imp;
    this->on_cntrl_force=cmd.on_cntr_force;
}

void CmdSkill::stop(const Percept& p){
    this->TF_T_EE_d=p.TF_T_EE;
    this->TF_dX_d.setZero();
    this->TF_F_d.setZero();
    this->TF_F_ff.setZero();
    this->q_d=p.q;
    this->dq_d.setZero();
    this->tau_d.setZero();
    this->tau_ff.setZero();
}

void CmdSkill::read_from_buffer(){
    this->TF_T_EE_d=this->TF_T_EE_d_buffer;
    this->TF_dX_d=this->TF_dX_d_buffer;
    this->TF_F_d=this->TF_F_d_buffer;
    this->TF_F_ff=this->TF_F_ff_buffer;
    this->K_x=this->K_x_buffer;
    this->xi_x=this->xi_x_buffer;

    this->q_d=this->q_d_buffer;
    this->dq_d=this->dq_d_buffer;
    this->tau_d=this->tau_d_buffer;
    this->tau_ff=this->tau_ff_buffer;
    this->K_theta=this->K_theta_buffer;
    this->xi_theta=this->xi_theta_buffer;
}

void CmdSkill::limit_output(const ConfigLimits& config){
    // Check for joint pose limits
    for(unsigned i=0;i<7;i++){
        if(this->q_d[i]>config.q_upper(i)){
            this->q_d[i]=config.q_upper(i);
        }
        if(this->q_d[i]<config.q_lower(i)){
            this->q_d[i]=config.q_lower(i);
        }
    }

    // Check for joint velocity limits
    for(unsigned i=0;i<7;i++){
        if(this->dq_d(i)>config.dq_max(i)){
            this->dq_d(i)=config.dq_max(i);
        }
        if(this->dq_d(i)<-config.dq_max(i)){
            this->dq_d(i)=-config.dq_max(i);
        }
    }

    // Check for joint stiffness limits
    for(unsigned i=0;i<7;i++){
        if(this->K_theta(i)>config.K_theta_max(i)){
            this->K_theta(i)=config.K_theta_max(i);
        }
        if(this->K_theta(i)<0){
            this->K_theta(i)=0;
        }
        if(this->xi_theta(i)>config.xi_theta_max(i)){
            this->xi_theta(i)=config.xi_theta_max(i);
        }
        if(this->xi_theta(i)<0){
            this->xi_theta(i)=0;
        }
    }

    // Check for Cartesian pose limits
    for(unsigned i=0;i<3;i++){
        if(this->TF_T_EE_d(i,3)>config.x_upper(i)){
            this->TF_T_EE_d(i,3)=config.x_upper(i);
        }
        if(this->TF_T_EE_d(i,3)<config.x_lower(i)){
            this->TF_T_EE_d(i,3)=config.x_lower(i);
        }
    }

    // Check for Cartesian stiffness limits
    for(unsigned i=0;i<6;i++){
        if(this->K_x(i)>config.K_x_max(i)){
            this->K_x(i)=config.K_x_max(i);
        }
        if(this->K_x(i)<0){
            this->K_x(i)=0;
        }
        if(this->xi_x(i)>config.xi_x_max(i)){
            this->xi_x(i)=config.xi_x_max(i);
        }
        if(this->xi_x(i)<0){
            this->xi_x(i)=0;
        }
    }

    // Check for Cartesian velocity limits
    for(unsigned i=0;i<3;i++){
        if(this->TF_dX_d(i)>config.dX_max(0)){
            this->TF_dX_d(i)=config.dX_max(0);
        }
        if(this->TF_dX_d(i)<-config.dX_max(0)){
            this->TF_dX_d(i)=-config.dX_max(0);
        }
        if(this->TF_dX_d(i+3)>config.dX_max(1)){
            this->TF_dX_d(i+3)=config.dX_max(1);
        }
        if(this->TF_dX_d(i+3)<-config.dX_max(1)){
            this->TF_dX_d(i+3)=-config.dX_max(1);
        }
    }
}

void CmdSkill::limit_output_rate(const ConfigLimits& config){
    for(unsigned i=0;i<3;i++){
        double diff_dX_t = this->TF_dX_d(i)-this->TF_dX_d_limiter[i];
        double diff_dX_r = this->TF_dX_d(i+3)-this->TF_dX_d_limiter[i+3];
        double diff_dF_t = this->TF_F_d(i)-this->TF_F_d_limiter(i);
        double diff_dF_r = this->TF_F_d(i+3)-this->TF_F_d_limiter(i+3);
        double diff_dF_ff_t = this->TF_F_ff(i)-this->TF_F_ff_limiter(i);
        double diff_dF_ff_r = this->TF_F_ff(i+3)-this->TF_F_ff_limiter(i+3);
        if(fabs(diff_dX_t)/0.001>config.ddX_max[0]){
            this->TF_dX_d(i)=this->TF_dX_d_limiter(i)+cpp_utils::sgn(diff_dX_t)*config.ddX_max(0)*0.001;
        }
        if(fabs(diff_dX_r)/0.001>config.ddX_max[1]){
            this->TF_dX_d(i+3)=this->TF_dX_d_limiter(i+3)+cpp_utils::sgn(diff_dX_r)*config.ddX_max(1)*0.001;
        }
        if(fabs(diff_dF_t)/0.001>config.dF_J_max[0]){
            this->TF_F_d(i)=this->TF_F_d_limiter(i)+cpp_utils::sgn(diff_dF_t)*config.dF_J_max(0)*0.001;
        }
        if(fabs(diff_dF_r)/0.001>config.dF_J_max[1]){
            this->TF_F_d(i+3)=this->TF_F_d_limiter(i+3)+cpp_utils::sgn(diff_dF_r)*config.dF_J_max(1)*0.001;
        }
        if(fabs(diff_dF_ff_t)/0.001>config.dF_J_max[0]){
            this->TF_F_ff(i)=this->TF_F_ff_limiter(i)+cpp_utils::sgn(diff_dF_ff_t)*config.dF_J_max(0)*0.001;
        }
        if(fabs(diff_dF_ff_r)/0.001>config.dF_J_max[1]){
            this->TF_F_ff(i+3)=this->TF_F_ff_limiter(i+3)+cpp_utils::sgn(diff_dF_ff_r)*config.dF_J_max(1)*0.001;
        }
    }

    for(unsigned i=0;i<6;i++){
        double diff_K_x = this->K_x(i)-this->K_x_limiter[i];
        double diff_xi_x = this->xi_x(i)-this->xi_x_limiter[i];
        if(fabs(diff_K_x)/0.001>config.dK_x_max[i]){
            this->K_x(i)=this->K_x_limiter(i)+cpp_utils::sgn(diff_K_x)*config.dK_x_max(i)*0.001;
        }
        if(fabs(diff_xi_x)/0.001>config.dxi_x_max[i]){
            this->xi_x(i)=this->xi_x_limiter(i)+cpp_utils::sgn(diff_xi_x)*config.dxi_x_max(i)*0.001;
        }
    }


    for(unsigned i=0;i<7;i++){
        double diff_q = this->q_d(i)-this->q_d_limiter(i);
        double diff_dq = this->dq_d(i)-this->dq_d_limiter(i);
        double diff_tau = this->tau_d(i)-this->tau_d_limiter(i);
        double diff_tau_ff = this->tau_ff(i)-this->tau_ff_limiter(i);
        double diff_K_theta = this->K_theta(i)-this->K_theta_limiter(i);
        double diff_xi_theta = this->xi_theta(i)-this->xi_theta_limiter(i);
        if(fabs(diff_q)/0.001>config.dq_max(i)){
            this->q_d(i)=this->q_d_limiter(i)+cpp_utils::sgn(diff_q)*config.dq_max(i)*0.001;
        }
        if(fabs(diff_dq)/0.001>config.ddq_max(i)){
            this->dq_d(i)=this->dq_d_limiter(i)+cpp_utils::sgn(diff_dq)*config.ddq_max(i)*0.001;
        }
        if(fabs(diff_tau)/0.001>config.tau_J_max(i)){
            this->tau_d(i)=this->tau_d_limiter(i)+cpp_utils::sgn(diff_tau)*config.tau_J_max(i)*0.001;
        }
        if(fabs(diff_tau_ff)/0.001>config.tau_J_max(i)){
            this->tau_ff(i)=this->tau_ff_limiter(i)+cpp_utils::sgn(diff_tau_ff)*config.tau_J_max(i)*0.001;
        }
        if(fabs(diff_K_theta)/0.001>config.dK_theta_max(i)){
            this->K_theta(i)=this->K_theta_limiter(i)+cpp_utils::sgn(diff_K_theta)*config.dK_theta_max(i)*0.001;
        }
        if(fabs(diff_xi_theta)/0.001>config.dxi_theta_max(i)){
            this->xi_theta(i)=this->xi_theta_limiter(i)+cpp_utils::sgn(diff_xi_theta)*config.dxi_theta_max(i)*0.001;
        }
    }
    this->TF_dX_d_limiter=this->TF_dX_d;
    this->TF_F_d_limiter=this->TF_F_d;
    this->TF_F_ff_limiter=this->TF_F_ff;
    this->K_x_limiter=this->K_x;
    this->xi_x_limiter=this->xi_x;

    this->q_d_limiter=this->q_d;
    this->dq_d_limiter=this->dq_d;
    this->tau_d_limiter=this->tau_d;
    this->tau_ff_limiter=this->tau_ff;
    this->K_theta_limiter=this->K_theta;
    this->xi_theta_limiter=this->xi_theta;
}

void CmdSkill::set_0(const Percept &p){
    this->q_d=p.q;
    this->q_d_buffer=p.q;
    this->q_d_limiter=p.q;

    this->TF_T_EE_d=p.TF_T_EE;
    this->TF_T_EE_d_limiter=p.TF_T_EE;
    this->TF_T_EE_d_buffer=p.TF_T_EE;

    this->K_x=p.K_x;
    this->K_x_buffer=p.K_x;
    this->K_x_limiter=p.K_x;
    this->xi_x=p.xi_x;
    this->xi_x_buffer=p.xi_x;
    this->xi_x_limiter=p.xi_x;

    this->K_theta=p.K_theta;
    this->K_theta_buffer=p.K_theta;
    this->K_theta_limiter=p.K_theta;
    this->xi_theta=p.xi_theta;
    this->xi_theta_buffer=p.xi_theta;
    this->xi_theta_limiter=p.xi_theta;
}

void CmdSkill::reset(){
    this->TF_T_EE_d=Eigen::Matrix<double,4,4>::Identity();
    this->TF_dX_d.setZero();
    this->TF_F_d.setZero();
    this->TF_F_ff.setZero();
    this->K_x.setZero();
    this->xi_x.setZero();
    this->TF_T_EE_d_buffer=Eigen::Matrix<double,4,4>::Identity();
    this->TF_dX_d_buffer.setZero();
    this->TF_F_d_buffer.setZero();
    this->TF_F_ff_buffer.setZero();
    this->K_x_buffer.setZero();
    this->xi_x_buffer.setZero();
    this->TF_T_EE_d_limiter=Eigen::Matrix<double,4,4>::Identity();
    this->TF_dX_d_limiter.setZero();
    this->TF_F_d_limiter.setZero();
    this->TF_F_ff_limiter.setZero();
    this->K_x_limiter.setZero();
    this->xi_x_limiter.setZero();

    this->q_d.setZero();
    this->q_d_buffer.setZero();
    this->q_d_limiter.setZero();
    this->dq_d.setZero();
    this->dq_d_buffer.setZero();
    this->dq_d_limiter.setZero();
    this->tau_d.setZero();
    this->tau_d_buffer.setZero();
    this->tau_d_limiter.setZero();
    this->tau_ff.setZero();
    this->tau_ff_buffer.setZero();
    this->tau_ff_limiter.setZero();
    this->K_theta.setZero();
    this->K_theta_buffer.setZero();
    this->K_theta_limiter.setZero();
    this->xi_theta.setZero();
    this->xi_theta_buffer.setZero();
    this->xi_theta_limiter.setZero();

    this->flag_stop=false;

    this->on_cntrl_imp=true;
    this->on_cntrl_force=true;
}

bool CmdSkill::validity_check(){
    for(unsigned i=0;i<7;i++){
        if(this->q_d(i)!=this->q_d(i)){
            cpp_utils::print_error("Detected NaN in skill command at q_d["+std::to_string(i)+"].");
            return false;
        }
        if(this->dq_d(i)!=this->dq_d(i)){
            cpp_utils::print_error("Detected NaN in skill command at dq_d["+std::to_string(i)+"].");
            return false;
        }
        if(this->tau_d(i)!=this->tau_d(i)){
            cpp_utils::print_error("Detected NaN in skill command at tau_d["+std::to_string(i)+"].");
            return false;
        }
        if(this->tau_ff(i)!=this->tau_ff(i)){
            cpp_utils::print_error("Detected NaN in skill command at tau_ff["+std::to_string(i)+"].");
            return false;
        }
        if(this->K_theta(i)!=this->K_theta(i)){
            cpp_utils::print_error("Detected NaN in skill command at K_theta["+std::to_string(i)+"].");
            return false;
        }
        if(this->xi_theta(i)!=this->xi_theta(i)){
            cpp_utils::print_error("Detected NaN in skill command at xi_theta["+std::to_string(i)+"].");
            return false;
        }
    }
    for(unsigned i=0;i<6;i++){
        if(this->TF_dX_d(i)!=this->TF_dX_d(i)){
            cpp_utils::print_error("Detected NaN in skill command at TF_dX_d["+std::to_string(i)+"].");
            return false;
        }
        if(this->TF_F_d(i)!=this->TF_F_d(i)){
            cpp_utils::print_error("Detected NaN in skill command at TF_F_d["+std::to_string(i)+"].");
            return false;
        }
        if(this->TF_F_ff(i)!=this->TF_F_ff(i)){
            cpp_utils::print_error("Detected NaN in skill command at TF_F_ff["+std::to_string(i)+"].");
            return false;
        }
        if(this->K_x(i)!=this->K_x(i)){
            cpp_utils::print_error("Detected NaN in skill command at K_x["+std::to_string(i)+"].");
            return false;
        }
        if(this->xi_x(i)!=this->xi_x(i)){
            cpp_utils::print_error("Detected NaN in skill command at xi_x["+std::to_string(i)+"].");
            return false;
        }
    }
    for(unsigned i=0;i<4;i++){
        for(unsigned j=0;j<4;j++){
            if(this->TF_T_EE_d(i)!=this->TF_T_EE_d(i)){
                cpp_utils::print_error("Detected NaN in skill command at TF_T_EE_d["+std::to_string(i)+","+std::to_string(j)+"].");
                return false;
            }
        }
    }
    if(!cpp_utils::is_orthonormal(this->TF_T_EE_d.block<3,3>(0,0))){
        cpp_utils::print_error("Rotation part of TF_T_EE_d is not orthonormal.");
        return false;
    }
    return true;
}


Skill::Skill(const std::string &type):_type(type){
    this->reset();
    this->_config=nullptr;
    this->_kb=nullptr;
}

Skill::~Skill(){

}

void Skill::reset(){
    for(auto& mp : this->_mp){
        mp.second->reset();
    }
    this->_active_mp=nullptr;
    this->_flag_init=true;
    this->_flag_terminate=false;
    this->_flag_aborted=false;
    this->_flag_fade_out=false;
    this->_flag_success=false;
    this->_flag_pause=false;
    this->_flag_invoke_failure=false;
    this->_flag_invoke_success=false;
    this->_flag_parallels_running=false;

    this->_eval.success=false;
    this->_eval.cost_err=0;
    this->_eval.cost_suc=0;
    this->_eval.results=nlohmann::json();
}

std::shared_ptr<ManipulationPrimitive> Skill::get_mp(const std::string &mp) const{
    if(this->_mp.find(mp)==this->_mp.end()){
        throw SkillException("No MP with id "+mp+" is contained within skill of type "+this->_type+". Check the skill implementation.");
    }
    return this->_mp.at(mp);
}

Eigen::Matrix<double,4,4> Skill::get_object_pose(const std::string &o, bool TF){
    if(this->_kb==nullptr){
        throw SkillException("Can not access knowledge base during task initialization in function get_object_pose.");
    }
    if(TF){
        return this->_kb->transform_to_EE(cpp_utils::rotate_matrix(this->get_object(o).O_T_o,cpp_utils::invert_matrix(this->_config->frames.O_R_TF)));
    }else{
        return this->_kb->transform_to_EE(this->get_object(o).O_T_o);
    }
}

const Object& Skill::get_object(const std::string &o) const{
    if(this->_objects.find(o)==this->_objects.end()){
        throw SkillException("No object of type "+o+" in skill "+ this->get_id() +" of type "+this->_type+" has been assigned. "
                                                                                                          "Check the task description or assign it manually in the task implementation.");
    }
    return this->_objects.at(o);
}

void Skill::write_O_R_TF(const Percept &p){
    if(!this->get_O_R_TF(p).isZero(0)){
        this->_config->frames.O_R_TF=this->get_O_R_TF(p);
    }
}

bool Skill::initialize(const Percept &p){
    if(this->_config==nullptr){
        cpp_utils::print_error("Skill with id "+this->_id+" has invalid configuration (nullptr). Stopping task.");
        return false;
    }
    //    if(!this->get_O_R_TF(p).isZero(0)){
    //        this->_config->frames.O_R_TF=this->get_O_R_TF(p);
    //    }
    if(!cpp_utils::is_orthonormal(this->_config->frames.O_R_TF)){
        cpp_utils::print_error("O_R_TF of skill "+this->_id+" is invalid. Aborting execution.");
        std::cout<<"O_R_TF: "<<this->_config->frames.O_R_TF<<std::endl;
        return false;
    }
    this->_mp.clear();
    this->_active_mp=nullptr;
    this->build_primitives(p);

    for(auto& mp : this->_mp){
        if(!mp.second->check_attractor()){
            cpp_utils::print_error("Attractor is invalid in skill of type "+this->_type+".");
            return false;
        }
    }
    this->_flag_fade_out=false;
    this->_cmd.reset();
    this->_cmd.set_0(p);

    if(this->_init_mp.empty()){
        cpp_utils::print_error("No initial manipulation primitive was selected in skill of type "+this->_type+".");
        return false;
    }
    this->_active_mp=this->get_mp(this->_init_mp);

    return true;
}

const CmdSkill& Skill::cycle(const Percept &p){
    // check: if mp not set return and stop
    if(this->_active_mp==nullptr){
        cpp_utils::print_error("No active manipulation primitive selected.");
        this->_cmd.flag_stop=true;
        return this->_cmd;
    }

    // set terminal percept to current percept (in case of non-nominal termination of skill)
    this->_eval.p_1=p;
    this->_active_mp->set_time(p.time);
    if(this->_active_mp->get_flag_error()){
        this->_flag_fade_out=true;
    }

    // if skill is in init state and check pre conditions
    if(this->_flag_init){
        if(!this->check_local_pre_conditions(p)){
            this->_flag_fade_out=true;
            this->_eval.success=false;
            this->_active_mp->terminate();
            this->_active_mp->set_flag_terminate();
            this->_cmd.read_from_buffer();
        }
        this->_eval.config=this->_config;
        this->_eval.p_0=p;
        this->_time_start=p.time;
        this->_active_mp->reset();
        this->_active_mp->set_0(p);
        this->_flag_init=false;
        this->_flag_parallels_running=true;
        this->_thr_parallels=std::thread(&Skill::run_parallels,this);
        this->_thr_parallels.detach();
    }
    auto edges_res=this->check_edges(p);
    if(this->_flag_fade_out){
        this->_cmd.stop(p);
    }else if(this->_active_mp->get_flag_init()){
        this->_active_mp->initialize(p,std::make_shared<ConfigUser>(this->_config->user));
        this->_cmd.read_from_buffer();
    }
    else if(std::get<0>(edges_res)){
        this->_active_mp->terminate();
        this->_active_mp->set_flag_terminate();
        this->_cmd.read_from_buffer();
        this->_eval.percepts.insert(std::pair<std::string,Percept>(this->_active_mp->get_id(),p));
        if(this->_mp.find(std::get<1>(edges_res))==this->_mp.end()){
            cpp_utils::print_warning("MP "+std::get<1>(edges_res)+" does not exist, terminating skill.");
            this->_flag_fade_out=true;
            this->_eval.success=false;
            this->_active_mp->terminate();
            this->_active_mp->set_flag_terminate();
            this->_cmd.read_from_buffer();
        }else{
            this->_active_mp=this->_mp[std::get<1>(edges_res)];
            this->_active_mp->reset();
            this->_active_mp->set_0(p);
        }
    }
    else{
        this->auxiliaries(p);
        if(this->_flag_pause){
            this->_cmd.stop(p);
        }else{
            this->_cmd.read_mp_cmd(this->_active_mp->step(p));
        }
    }
    if(!this->_flag_fade_out && (this->check_global_err_conditions(p) || this->check_local_err_conditions(p))){
        cpp_utils::print_warning("Error conditions of skill "+this->_id+" have been triggered.");
        this->_flag_fade_out=true;
        this->_eval.success=false;
        this->_active_mp->terminate();
        this->_active_mp->set_flag_terminate();
        this->_cmd.read_from_buffer();

    }
    else if(!this->_flag_fade_out && (this->check_local_suc_conditions(p) || this->check_global_suc_conditions(p))){
        this->_flag_success=true;
    }
    if(this->check_local_ex_conditions(p) && this->_flag_success && !this->_flag_fade_out){
        cpp_utils::print_success("Exit condition of skill "+this->_id+" has been triggered after success.");
        this->_active_mp->terminate();
        this->_active_mp->set_flag_terminate();
        this->_flag_fade_out=true;
        this->_eval.success=true;
    }
    this->_cmd.limit_output_rate(this->_kb->get_local_memory()->access_config_limits());
    this->_cmd.limit_output(this->_kb->get_local_memory()->access_config_limits());
    if(this->_flag_fade_out){
        bool all_zero=true;
        for(unsigned i=0;i<3;i++){
            if(fabs(this->_cmd.TF_dX_d(i))>this->_config->limits.ddX_max(0)/1000/2 ||
                    fabs(this->_cmd.TF_F_d(i))>this->_config->limits.dF_J_max(0)/1000/2 ||
                    fabs(this->_cmd.TF_F_ff(i))>this->_config->limits.dF_J_max(0)/1000/2){
                all_zero=false;
                break;
            }
        }
        for(unsigned i=3;i<6;i++){
            if(fabs(this->_cmd.TF_dX_d(i))>this->_config->limits.ddX_max(1)/1000/2 ||
                    fabs(this->_cmd.TF_F_d(i))>this->_config->limits.dF_J_max(1)/1000/2 ||
                    fabs(this->_cmd.TF_F_ff(i))>this->_config->limits.dF_J_max(1)/1000/2){
                all_zero=false;
                break;
            }
        }
        if(all_zero){
            cpp_utils::print_info("Skill "+this->_id+" has terminated.");
            this->terminate_parallels();
            this->_flag_terminate=true;
        }
    }

    return this->_cmd;
}

void Skill::stop_skill(){
    this->_flag_aborted=true;
    this->_flag_fade_out=true;
}

void Skill::set_pause(bool pause){
    this->_flag_pause=pause;
}

void Skill::append_error(const std::string& error){
    this->_eval.last_errors.push_back(error);
}

Eigen::Matrix<double,3,3> Skill::get_O_R_TF(const Percept &p){
    Eigen::Matrix<double,3,3> O_R_TF;
    O_R_TF.setZero();
    return O_R_TF;
}

void Skill::set_init_mp(const std::string &id){
    if(this->_mp.find(id)==this->_mp.end()){
        throw SkillException("Could not set initial manipulation primitive in skill of type "+this->_type+". MP with id "+id+"not found in skill.");
    }else{
        this->_active_mp=this->_mp[id];
        this->_init_mp=id;
    }
}

//void Skill::insert_mp(std::string id, std::shared_ptr<ManipulationPrimitive> mp, const Percept& p){
//    mp->set_id(id);
//    if(this->_mp.find(id)!=this->_mp.end()){
//        throw SkillException("Could not insert new manipulation primitive. MP with id "+id+" already exists.");
//    }else{
//        this->_mp.insert(std::pair<std::string,std::shared_ptr<ManipulationPrimitive> >(id,mp));
//        this->_mp[id]->get_attractor()->reset();
//        this->_mp[id]->init_attractor(p,std::make_shared<ConfigUser>(this->_config->user));
//    }
//}

void Skill::terminate(){

    for(auto& mp : this->_mp){
        if(!mp.second->get_flag_terminate()){
            mp.second->terminate();
        }
        mp.second->write_logs();
    }
    this->evaluate();
    if(this->_flag_aborted){
        cpp_utils::print_info("Skill "+this->_id+" has been aborted.");
    }else{
        if(this->_eval.success){
            cpp_utils::print_success("Skill "+this->_id+" was successful.");
        }else{
            cpp_utils::print_error("Skill "+this->_id+" has failed.");
        }
    }
}

void Skill::invoke_failure(){
    this->_flag_invoke_failure=true;
}

void Skill::invoke_success(){
    this->_flag_invoke_success=true;
}

bool Skill::check_global_err_conditions(const Percept& p){
    if(this->_config==nullptr){
        throw SkillException("Config in skill "+this->_id+" has not been set. Check the function <create_config> in the skill implementation.");
    }
    for(unsigned i=0;i<6;i++){
        if(fabs(p.TF_F_ext(i))>=this->_config->user.F_max[i]){
            cpp_utils::print_error("Skill "+this->_id+" has violated the maximum allowed external cartesian forces.");
            std::cout<<"F_ext: "<<p.TF_F_ext<<std::endl;
            return true;
        }
    }
    for(unsigned i=0;i<7;i++){
        if(fabs(p.tau_ext(i))>=this->_config->user.tau_max[i]){
            cpp_utils::print_error("Skill "+this->_id+" has violated the maximum allowed external joint torques at joint "+std::to_string(i)+".");
            std::cout<<"tau_ext: "<<p.tau_ext<<std::endl;
            return true;
        }
    }
    for(unsigned i=0;i<7;i++){
        if(fabs(p.tau_ext[i])>=this->_config->limits.tau_ext_max[i]){
            cpp_utils::print_error("Skill "+this->_id+" has violated the maximum external joint torques at joint "+std::to_string(i)+".");
            return true;
        }
    }
    if(p.time-this->_time_start>this->_config->time_max && this->_config->time_max>0){
        cpp_utils::print_error("Skill "+this->_id+" has violated the maximum time limit of "+std::to_string(this->_config->time_max)+" s.");
        return true;
    }
    if(this->_flag_invoke_failure){
        cpp_utils::print_error("Failure has been invoked externally");
        return true;
    }
    return false;
}

bool Skill::check_global_suc_conditions(const Percept &p) const{
    if(this->_flag_invoke_success){
        cpp_utils::print_success("Success has been invoked externally");
        return true;
    }
    return false;
}

double Skill::get_t_init() const{
    return this->_time_start;
}

bool Skill::check_local_pre_conditions(const Percept &p){
    return true;
}

bool Skill::check_local_err_conditions(const Percept &p){
    return false;
}

bool Skill::check_local_ex_conditions(const Percept &p){
    return true;
}

//std::shared_ptr<ConfigSkill> Skill::get_config(){
//    if(this->_config==nullptr){
//        throw SkillException("Can not access skill configuration during task initialization.");
//    }
//    return this->_config;
//}

const EvalSkill &Skill::get_eval() const{
    return this->_eval;
}

bool Skill::get_flag_terminate() const{
    return this->_flag_terminate;
}

const std::string& Skill::get_type() const{
    return this->_type;
}

const std::string& Skill::get_id() const{
    return this->_id;
}

void Skill::set_id(const std::string& id){
    this->_id=id;
}

void Skill::set_kb(std::shared_ptr<KnowledgeBase> kb){
    this->_kb=kb;
}

void Skill::read_configuration(const nlohmann::json &p){
    if(cpp_utils::find_json_value(p,"controller")){
        this->_config->controller.read_parameters(p["controller"]);
    }
    if(cpp_utils::find_json_value(p,"frames")){
        this->_config->frames.read_parameters(p["frames"]);
    }
    if(cpp_utils::find_json_value(p,"general")){
        this->_config->general.read_parameters(p["general"]);
    }
    if(cpp_utils::find_json_value(p,"system")){
        this->_config->system.read_parameters(p["system"]);
    }
    if(cpp_utils::find_json_value(p,"user")){
        this->_config->user.read_parameters(p["user"]);
    }
    if(cpp_utils::find_json_value(p,"skill")){
        this->read_global_skill_parameters(p["skill"]);
    }
}

void Skill::read_global_skill_parameters(const nlohmann::json &p){
    cpp_utils::read_json_param(p,"time_max",this->_config->time_max);
    cpp_utils::read_json_param(p,"w_cost_function",this->_config->w_cost_function);
    cpp_utils::read_json_param(p,"parallels_frequency",this->_config->parallels_frequency);
    cpp_utils::read_json_param<double,6,1>(p,"k_h_p",this->_config->k_h_p);
    cpp_utils::read_json_param<double,6,1>(p,"k_h_d",this->_config->k_h_d);
}

void Skill::set_object(const std::string& o_type, const std::string& o){
    if(this->_kb==nullptr){
        throw SkillException("Can not access knowledge base during task initialization in function set_object.");
    }
    if(o==""){
        throw SkillException("Function set_object was called for skill "+this->_id+" and object type " + o_type + " with an empty object id.");
    }
    Object obj;
    if(!this->_kb->load_object(o,obj)){
        throw SkillException("Object with id "+o+" required by skill "+this->_id+" does not exist in knowledge base.");
    }
    if(this->_objects.find(o_type)==this->_objects.end()){
        throw SkillException("Skill "+this->_id+" of type "+this->_type+" has no object of type "+o_type+".");
    }
    this->_objects[o_type]=obj;
}

void Skill::set_object(const std::string &o_type, const Object &o){
    if(this->_kb==nullptr){
        throw SkillException("Can not access knowledge base during task initialization in function set_object.");
    }
    this->_objects[o_type]=o;
}

bool Skill::load_objects(const std::map<std::string, std::string>& objects){
    if(this->_kb==nullptr){
        throw SkillException("Can not access knowledge base during task initialization in function load_objects.");
    }
    this->_objects.clear();
    for(auto& o : objects){
        Object obj;
        if(!this->_kb->load_object(o.second,obj)){
            cpp_utils::print_error("Could not load "+o.second+" as type " +o.first+".");
            return false;
        }
        this->_objects.insert(std::pair<std::string,Object>(o.first,obj));
    }
    return true;
}

void Skill::auxiliaries(const Percept &p){

}

void Skill::parallels(){

}

void Skill::run_parallels(){
    while(!this->_flag_terminate){
        auto start = std::chrono::high_resolution_clock::now();
        this->parallels();
        auto finish = std::chrono::high_resolution_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(finish - start);
        double t_sleep_max = 1.0/this->_config->parallels_frequency;

        std::this_thread::sleep_for(std::chrono::microseconds(long(t_sleep_max*1000000-elapsed.count())));
        if(!this->_flag_parallels_running){
            cpp_utils::print_info("Parallel thread has stopped.");
            return;
        }
    }
}

void Skill::terminate_parallels(){
    if(this->_thr_parallels.joinable()){
        this->_flag_parallels_running=false;
    }
}

}
