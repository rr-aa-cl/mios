#pragma once

#include <iostream>
#include <vector>

#include <eigen3/Eigen/Core>

#include "knowledge_base/local_memory.hpp"
#include "knowledge_base/knowledge_base.hpp"

namespace mios {

struct ConfigMP{

};

struct EvalMP{

};

struct CmdMP{
    CmdMP(){
        this->reset();
    }

    void reset(){
        this->TF_T_EE_d=Eigen::Matrix<double,4,4>::Identity();
        this->TF_dX_d.setZero();
        this->TF_F_d.setZero();
        this->TF_F_ff.setZero();

        this->q_d.setZero();
        this->dq_d.setZero();
        this->tau_d.setZero();
        this->tau_ff.setZero();

        this->on_cntr_imp=true;
        this->on_cntr_force=true;
    }

    void set_0(const Percept& p){
        this->TF_T_EE_d=p.TF_T_EE;
        this->TF_dX_d.setZero();
        this->TF_F_d.setZero();
        this->TF_F_ff.setZero();
        this->K_x=p.K_x;
        this->xi_x=p.xi_x;

        this->q_d=p.q_d;
        this->dq_d.setZero();
        this->tau_d.setZero();
        this->tau_ff.setZero();
        this->K_theta=p.K_theta;
        this->xi_theta=p.xi_theta;
    }

    Eigen::Matrix<double,4,4> TF_T_EE_d;
    Eigen::Matrix<double,6,1> TF_dX_d;
    Eigen::Matrix<double,6,1> TF_F_d;
    Eigen::Matrix<double,6,1> TF_F_ff;
    Eigen::Matrix<double,6,1> K_x;
    Eigen::Matrix<double,6,1> xi_x;

    Eigen::Matrix<double,7,1> q_d;
    Eigen::Matrix<double,7,1> dq_d;
    Eigen::Matrix<double,7,1> tau_d;
    Eigen::Matrix<double,7,1> tau_ff;
    Eigen::Matrix<double,7,1> K_theta;
    Eigen::Matrix<double,7,1> xi_theta;

    bool on_cntr_imp;
    bool on_cntr_force;
};

struct Attractor{
    virtual void reset() = 0;
};

class ManipulationPrimitive{
public:
    ManipulationPrimitive(const std::string& type);
    virtual ~ManipulationPrimitive();

    bool get_flag_init() const;
    bool get_flag_terminate() const;
    void set_flag_terminate();
    bool get_flag_error() const;
    void set_flag_error();
    std::string get_type() const;
    std::string get_id() const;

    void set_id(const std::string& id);
    void set_kb(std::shared_ptr<KnowledgeBase> kb);

    void reset();
    void set_0(const Percept& p);

    virtual void initialize(const Percept& p_0,const std::shared_ptr<ConfigUser> config) = 0;
    virtual CmdMP& step(const Percept& p) = 0;
    virtual void terminate() = 0;

    virtual bool in_attractor(const Percept& p) = 0;
    virtual bool check_attractor() = 0;
    virtual bool init_attractor(const Percept& p,const std::shared_ptr<ConfigUser> config) = 0;

    virtual void setup_logs(unsigned long long length) = 0;
    virtual void write_logs() = 0;

    void set_time(double t);
    double get_time() const;

    std::shared_ptr<ConfigMP> get_config() const;
    std::shared_ptr<Attractor> get_attractor() const;
    std::shared_ptr<EvalMP> get_eval() const;
protected:

    std::shared_ptr<ConfigMP> _config;
    std::shared_ptr<EvalMP> _eval;
    CmdMP _cmd;

    std::shared_ptr<Attractor> _attractor;
    std::shared_ptr<KnowledgeBase> _kb;

    std::string _type;
    std::string _id;

    bool _flag_init;
    bool _flag_terminate;
    bool _flag_error;

    double _time;
    unsigned long long _step;
    bool _log;

};

}
