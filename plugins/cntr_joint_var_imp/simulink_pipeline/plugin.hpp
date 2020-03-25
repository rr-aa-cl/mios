#pragma once

#include <vector>
#include <string>

#include <eigen3/Eigen/Core>

struct In_U{

};

struct In_P{

};

struct Out_Y{

};

struct Out_L{

};


class Plugin{
public:
    Plugin();
    virtual ~Plugin();

    virtual void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="") = 0;
    virtual void step(const In_U& in_u,Out_Y& out_y) = 0;
    virtual void terminate() = 0;

protected:

    virtual void write_params_to_model() = 0;
    virtual void write_logs() = 0;



    In_P* _in_p;

    std::string _path_logs;
    unsigned long long _cnt_step;
    bool _flag_log;

};
