#include "manipulation_primitive/manipulation_primitive.hpp"

namespace mios {

ManipulationPrimitive::ManipulationPrimitive(const std::string &type):_type(type){
    this->_eval=nullptr;
    this->_config=nullptr;
    this->_attractor=nullptr;
    this->reset();
}

ManipulationPrimitive::~ManipulationPrimitive(){

}

void ManipulationPrimitive::reset(){
    this->_flag_init=true;
    this->_flag_terminate=false;
    this->_flag_error=false;
    this->_eval=nullptr;

    this->_log=false;
    this->_step=0;
    this->_time=0;

    this->_cmd.reset();
}

void ManipulationPrimitive::set_0(const Percept &p){
    this->_cmd.set_0(p);
}

std::string ManipulationPrimitive::get_type() const{
    return this->_type;
}

bool ManipulationPrimitive::get_flag_init() const{
    return this->_flag_init;
}

bool ManipulationPrimitive::get_flag_terminate() const{
    return this->_flag_terminate;
}

void ManipulationPrimitive::set_flag_terminate(){
    this->_flag_terminate=true;
}

bool ManipulationPrimitive::get_flag_error() const{
    return this->_flag_error;
}

void ManipulationPrimitive::set_flag_error(){
    this->_flag_error=true;
}

void ManipulationPrimitive::set_id(const std::string& id){
    this->_id=id;
}

void ManipulationPrimitive::set_kb(std::shared_ptr<KnowledgeBase> kb){
    this->_kb=kb;
}

std::string ManipulationPrimitive::get_id() const{
    return this->_id;
}

void ManipulationPrimitive::set_time(double t){
    this->_time=t;
}

double ManipulationPrimitive::get_time() const{
    return this->_time;
}

std::shared_ptr<ConfigMP> ManipulationPrimitive::get_config() const{
    return this->_config;
}

std::shared_ptr<Attractor> ManipulationPrimitive::get_attractor() const{
    return this->_attractor;
}

std::shared_ptr<EvalMP> ManipulationPrimitive::get_eval() const{
    return this->_eval;
}

}
