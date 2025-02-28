#include "mios/strategies/read_from_file_strategy.hpp"
#include "mirmi_cpp_utils/files/files.hpp"

#include <string>
#include <iostream>
#include <array>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <vector>
#include <sys/stat.h>
#include <unistd.h>
#include <cstring>

namespace mios{

ReadFromFileStrategy::ReadFromFileStrategy():PrimitiveStrategy({CommandPatternCartesianPose,CommandPatternJointPose}){
    m_joint_mode=false;
}

void ReadFromFileStrategy::initialize([[maybe_unused]] const Percept &p_0){
    m_cnt_data=0;
}

void ReadFromFileStrategy::set_joint_mode(){
    m_joint_mode=true;
}   

void ReadFromFileStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    if(m_joint_mode){
        if(m_cnt_data<m_data_joint.size()){
            cmd.q_d=Eigen::Matrix<double,7,1>(m_data_joint[m_cnt_data].data());
            m_cnt_data++;
        }
    }
    else{
        if(m_cnt_data<m_data.size()){
            cmd.TF_T_EE_d=Eigen::Matrix<double,4,4>(m_data[m_cnt_data].data());
            m_cnt_data++;
        }
    }

}

void ReadFromFileStrategy::terminate([[maybe_unused]] const Percept &p){
}

bool ReadFromFileStrategy::finished(){
    if(m_joint_mode){
        return m_cnt_data>=m_data_joint.size();
    }
    return m_cnt_data>=m_data.size();
}

void ReadFromFileStrategy::set_data(const std::vector<std::array<double,16> >& data){
    m_data=data;
}
void ReadFromFileStrategy::set_data(const std::vector<std::array<double,7> >& data){
    m_data_joint=data;
}


}
