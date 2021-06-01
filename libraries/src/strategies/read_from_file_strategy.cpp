#include "strategies/read_from_file_strategy.hpp"
#include "msrm_cpp_utils/files.hpp"

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

ReadFromFileStrategy::ReadFromFileStrategy():PrimitiveStrategy({CommandPatternCartesianPose}){

}

void ReadFromFileStrategy::initialize(const Percept &p_0){
    m_cnt_data=0;
}

void ReadFromFileStrategy::get_next_command(Actuator &cmd, const Percept &p){
    if(m_cnt_data<m_data.size()){
        cmd.TF_T_EE_d=Eigen::Matrix<double,4,4>(m_data[m_cnt_data].data());
        m_cnt_data++;
    }
}

void ReadFromFileStrategy::terminate(const Percept &p){
}

bool ReadFromFileStrategy::finished(){
    return m_cnt_data>=m_data.size();
}

void ReadFromFileStrategy::set_data(const std::vector<std::array<double,16> >& data){
    m_data=data;
}



}
