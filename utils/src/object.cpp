#include "data_structures/object.hpp"
#include <msrm_utils/json.hpp>
#include <spdlog/spdlog.h>

namespace mios {

Object::Object(const std::string name):name(name){
    q.setZero();
    O_T_OB=Eigen::Matrix<double,4,4>::Identity();
    OB_T_gp=Eigen::Matrix<double,4,4>::Identity();
    OB_T_TCP=Eigen::Matrix<double,4,4>::Identity();
    OB_I.setZero();
    grasp_width=0;
    grasp_force=0;
    mass=0;
    geometry=nlohmann::json();
}

nlohmann::json Object::to_json() const{
    nlohmann::json obj;
    obj["name"]=name;
    msrm_utils::write_json_array<double,4,4>(obj["O_T_OB"],O_T_OB);
    msrm_utils::write_json_array<double,7,1>(obj["q"],q);
    msrm_utils::write_json_array<double,4,4>(obj["OB_T_gp"],OB_T_gp);
    msrm_utils::write_json_array<double,4,4>(obj["OB_T_TCP"],OB_T_TCP);
    msrm_utils::write_json_array<double,3,3>(obj["OB_I"],OB_I);
    obj["grasp_width"]=grasp_width;
    obj["grasp_force"]=grasp_force;
    obj["mass"]=mass;
    obj["geometry"]=geometry;
    return obj;
}

Object Object::from_json(const nlohmann::json& p){
    try {
        std::string name;
        p["name"].get_to(name);
        Object o(name);
        msrm_utils::read_json_param<double,7,1>(p,"q",o.q);
        msrm_utils::read_json_param<double,4,4>(p,"O_T_OB",o.O_T_OB);
        msrm_utils::read_json_param<double,4,4>(p,"OB_T_gp",o.OB_T_gp);
        msrm_utils::read_json_param<double,4,4>(p,"OB_T_TCP",o.OB_T_TCP);
        msrm_utils::read_json_param(p,"grasp_width",o.grasp_width);
        msrm_utils::read_json_param(p,"grasp_force",o.grasp_force);
        msrm_utils::read_json_param(p,"mass",o.mass);
        msrm_utils::read_json_param<double,3,3>(p,"OB_I",o.OB_I);
        if(p.find("geometry")!=p.end()){
            o.geometry=p["geometry"];
        }
        return o;
    }catch(const nlohmann::detail::type_error& e){
        spdlog::debug(e.what());
        return Object("NullObject");
    }
}

}
