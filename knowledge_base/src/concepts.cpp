#include "knowledge_base/concepts.hpp"
#include <msrm_utils/output.hpp>

namespace mios {

Concept::Concept(std::string id){
    this->id=id;
}

Concept::~Concept(){

}

std::string Concept::get_id(){
    return this->id;
}

void Concept::from_json(const nlohmann::json &p){
    msrm_utils::read_json_param(p,"id",this->id);
}

nlohmann::json Concept::to_json(){
    nlohmann::json v;
    v["id"]=this->id;
    return v;
}

Spatial::Spatial(std::string id):Concept(id){

}

Spatial::~Spatial(){

}

void Spatial::from_json(const nlohmann::json &p){
    Concept::from_json(p);
    msrm_utils::read_json_param<double,4,4>(p,"O_T_S",this->O_T_S);
    msrm_utils::read_json_param<double,7,1>(p,"q",this->q);
}

nlohmann::json Spatial::to_json(){
    nlohmann::json v;
    msrm_utils::overwrite_valid_json(Concept::to_json(),v);
    msrm_utils::write_json_array<double,4,4>(v["O_T_S"],this->O_T_S);
    msrm_utils::write_json_array<double,7,1>(v["q"],this->q);
    return v;
}

const Eigen::Matrix<double,4,4>& Spatial::get_O_T_S(){
    return this->O_T_S;
}
Eigen::Matrix<double,4,4> Spatial::get_TF_T_S(const Eigen::Matrix<double,3,3>& O_R_TF){
    return msrm_utils::rotate_matrix(this->O_T_S,msrm_utils::invert_matrix(O_R_TF));
}
const Eigen::Matrix<double,7,1>& Spatial::get_q(){
    return this->q;
}

Inertial::Inertial(std::string id):Concept(id){

}

Inertial::~Inertial(){

}

void Inertial::from_json(const nlohmann::json &p){
    Concept::from_json(p);
    msrm_utils::read_json_param(p,"m",this->m);
    msrm_utils::read_json_param<double,3,1>(p,"com",this->com);
    msrm_utils::read_json_param<double,3,3>(p,"q",this->I);
}

nlohmann::json Inertial::to_json(){
    nlohmann::json v;
    msrm_utils::overwrite_valid_json(Concept::to_json(),v);
    v["m"]=this->m;
    msrm_utils::write_json_array<double,3,1>(v["com"],this->com);
    msrm_utils::write_json_array<double,3,3>(v["I"],this->I);
    return v;
}

double Inertial::get_m(){
    return this->m;
}

Eigen::Matrix<double,3,1> Inertial::get_com(){
    return this->com;
}
Eigen::Matrix<double,3,3> Inertial::get_I(){
    return this->I;
}

Geometry::Geometry(std::string id):Concept(id){

}

Geometry::~Geometry(){

}

void Geometry::from_json(const nlohmann::json &p){
    Concept::from_json(p);
}

nlohmann::json Geometry::to_json(){
    nlohmann::json v;
    msrm_utils::overwrite_valid_json(Concept::to_json(),v);
    return v;
}

Location::Location(std::string id):Spatial(id),Concept(id){

}

Location::~Location(){

}

nlohmann::json Location::to_json(){
    nlohmann::json v;
    msrm_utils::overwrite_valid_json(Spatial::to_json(),v);
    return v;
}

void Location::from_json(const nlohmann::json &p){
    Spatial::from_json(p);
}

PhysicalObject::PhysicalObject(std::string id):Spatial(id),Geometry(id),Inertial(id),Concept(id){

}

PhysicalObject::~PhysicalObject(){

}

nlohmann::json PhysicalObject::to_json(){
    nlohmann::json v;
    msrm_utils::overwrite_valid_json(Spatial::to_json(),v);
    msrm_utils::overwrite_valid_json(Geometry::to_json(),v);
    msrm_utils::overwrite_valid_json(Inertial::to_json(),v);
    return v;
}

void PhysicalObject::from_json(const nlohmann::json &p){
    Spatial::from_json(p);
    Geometry::from_json(p);
    Inertial::from_json(p);
}

Robot::Robot(std::string id):PhysicalObject(id),Concept(id){

}

Robot::~Robot(){

}

nlohmann::json Robot::to_json(){
    nlohmann::json v;
    msrm_utils::overwrite_valid_json(PhysicalObject::to_json(),v);
    v["hostname"]=this->hostname;
    return v;
}

void Robot::from_json(const nlohmann::json &p){
    PhysicalObject::from_json(p);
    msrm_utils::read_json_param(p,"hostname",this->hostname);
}

void Robot::set_ip(const std::string &ip){
    this->ip=ip;
}

void Robot::set_hostname(const std::string& hostname){
    this->hostname=hostname;
}

std::string Robot::get_hostname(){
    return this->hostname;
}

std::string Robot::get_ip(){
    return this->ip;
}

Object::Object(){
    this->EE_T_O<<1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1;
    this->grasp_width=0;
    this->mass=0;
    this->EE_ob_com<<0,0,0;
    this->ob_I<<0,0,0,0,0,0,0,0,0;
    this->EE_T_O<<1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1;
    this->geometry=nlohmann::json();
}

Object::~Object(){

}

nlohmann::json Object::to_json(){
    nlohmann::json obj;
    obj["name"]=name;
    msrm_utils::write_json_array<double,4,4>(obj["O_T_o"],O_T_o);
    msrm_utils::write_json_array<double,7,1>(obj["q_o"],q_o);
    msrm_utils::write_json_array<double,4,4>(obj["EE_T_O"],EE_T_O);
    msrm_utils::write_json_array<double,3,1>(obj["EE_ob_com"],EE_ob_com);
    msrm_utils::write_json_array<double,3,3>(obj["ob_I"],ob_I);
    obj["grasp_width"]=grasp_width;
    obj["mass"]=mass;
    obj["geometry"]=geometry;
    return obj;
}

void Object::from_json(const nlohmann::json& p){
    msrm_utils::read_json_param(p,"name",name);
    msrm_utils::read_json_param<double,7,1>(p,"q_o",q_o);
    msrm_utils::read_json_param<double,4,4>(p,"O_T_o",O_T_o);
    msrm_utils::read_json_param<double,4,4>(p,"EE_T_O",EE_T_O);
    msrm_utils::read_json_param(p,"grasp_width",grasp_width);
    msrm_utils::read_json_param(p,"mass",mass);
    msrm_utils::read_json_param<double,3,1>(p,"EE_ob_com",EE_ob_com);
    msrm_utils::read_json_param<double,3,3>(p,"ob_I",ob_I);
    if(msrm_utils::find_json_value(p,"geometry")){
        geometry=p["geometry"];
    }
}

Eigen::Matrix<double,4,4> Object::TF_T_o(const Eigen::Matrix<double,3,3>& O_R_TF){
    return msrm_utils::rotate_matrix(this->O_T_o,msrm_utils::invert_matrix(O_R_TF));
}

ReferenceFrame::ReferenceFrame(){
    this->O_T_f=Eigen::Matrix<double,4,4>::Identity();
}

ReferenceFrame::~ReferenceFrame(){

}

Eigen::Matrix<double,4,4> ReferenceFrame::get_relative_pose(const std::string& object){
    if(this->objects.find(object)!=this->objects.end()){
        msrm_utils::print_warning("Reference frame " + this->name + " is not connected to object " + object + ".");
        return Eigen::Matrix<double,4,4>::Identity();
    }
    Eigen::Matrix<double,4,4> DeltaT;
    if(!msrm_utils::read_json_param<double,4,4>(this->objects,object.c_str(),DeltaT)){
        msrm_utils::print_warning("Could not read relative pose of object " + object + ".");
        return Eigen::Matrix<double,4,4>::Identity();
    }
    return DeltaT;
}

nlohmann::json ReferenceFrame::to_json(){
    nlohmann::json frame;
    frame["name"]=name;
    msrm_utils::write_json_array<double,4,4>(frame["O_T_f"],O_T_f);
    frame["objects"]=objects;
    return frame;
}

void ReferenceFrame::from_json(const nlohmann::json &p){
    msrm_utils::read_json_param<double,4,4>(p,"O_T_f",O_T_f);
    if(msrm_utils::find_json_value(p,"objects")){
        objects=p["objects"];
    }
}

}
