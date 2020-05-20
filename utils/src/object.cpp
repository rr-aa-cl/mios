#include "data_structures/object.hpp"
#include <msrm_utils/json.hpp>

namespace mios {

Object::Object(const std::string name):name(name){
    q.setZero();
    O_T_OB=Eigen::Matrix<double,4,4>::Identity();
    OB_T_gp=Eigen::Matrix<double,4,4>::Identity();
    OB_I.setZero();
    this->grasp_width=0;
    this->mass=0;
    this->geometry=nlohmann::json();
}

nlohmann::json Object::to_json(){
    nlohmann::json obj;
    obj["name"]=name;
    msrm_utils::write_json_array<double,4,4>(obj["O_T_OB"],O_T_OB);
    msrm_utils::write_json_array<double,7,1>(obj["q"],q);
    msrm_utils::write_json_array<double,4,4>(obj["OB_T_gp"],OB_T_gp);
    msrm_utils::write_json_array<double,3,3>(obj["OB_I"],OB_I);
    obj["grasp_width"]=grasp_width;
    obj["mass"]=mass;
    obj["geometry"]=geometry;
    return obj;
}

void Object::from_json(const nlohmann::json& p){
    msrm_utils::read_json_param(p,"name",name);
    msrm_utils::read_json_param<double,7,1>(p,"q",q);
    msrm_utils::read_json_param<double,4,4>(p,"O_T_OB",O_T_OB);
    msrm_utils::read_json_param<double,4,4>(p,"OB_T_gp",OB_T_gp);
    msrm_utils::read_json_param(p,"grasp_width",grasp_width);
    msrm_utils::read_json_param(p,"mass",mass);
    msrm_utils::read_json_param<double,3,3>(p,"OB_I",OB_I);
    if(p.find("geometry")!=p.end()){
        geometry=p["geometry"];
    }
}

}
