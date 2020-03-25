#include "knowledge_base/knowledge_base.hpp"

#include <bsoncxx/json.hpp>
#include <bsoncxx/builder/basic/array.hpp>
#include <bsoncxx/builder/basic/document.hpp>
#include <bsoncxx/builder/basic/kvp.hpp>
#include <bsoncxx/document/value.hpp>
#include <bsoncxx/stdx/string_view.hpp>
#include <bsoncxx/types.hpp>

#include "cpp_utils/math.hpp"
#include "cpp_utils/system.hpp"


#include "interface/parameter_server.hpp"


namespace mios {

KnowledgeBase::KnowledgeBase(){
    this->_live_parameters=nullptr;
    this->_client=nullptr;
}

LocalMemory* const KnowledgeBase::get_local_memory(){
    return &this->_local_memory;
}

void KnowledgeBase::set_live_parameter_server(std::shared_ptr<ParameterServer> server){
    this->_live_parameters=server;
}

nlohmann::json KnowledgeBase::get_live_parameter(const std::string& parameter) const{
    return this->_live_parameters->get_parameter(parameter);
}

std::string KnowledgeBase::get_event(const std::string& e) const{
    if(this->_event_memory.find(e)==this->_event_memory.end()){
        return "";
    }else{
        return this->_event_memory.at(e);
    }
    return "";
}

void KnowledgeBase::set_event(const std::string& e, const std::string& state){
    if(this->_event_memory.find(e)==this->_event_memory.end()){
        this->_event_memory.insert(std::pair<std::string,std::string>(e,state));
    }else{
        this->_event_memory[e]=state;
    }
}

bool KnowledgeBase::initialize(const ConfigInternal &config, unsigned port){
    try{
        this->_mtx_mongodb.lock();
        mongocxx::uri uri("mongodb://localhost:"+std::to_string(port));
        this->_client = std::make_unique<mongocxx::client>(uri);

        this->_db=this->_client->database("mios");
        if(!this->_db.has_collection("environment")){
            cpp_utils::print_error("Knowledge base does not have an environment collection");
            this->_mtx_mongodb.unlock();
            return false;
        }
        if(!this->_db.has_collection("reference_frames")){
            cpp_utils::print_error("Knowledge base does not have a reference_frames collection");
            this->_mtx_mongodb.unlock();
            return false;
        }
        if(!this->_db.has_collection("parameters")){
            cpp_utils::print_error("Knowledge base does not have a parameters collection");
            this->_mtx_mongodb.unlock();
            return false;
        }
        if(!this->_db.has_collection("skills")){
            cpp_utils::print_error("Knowledge base does not have a skills collection");
            this->_mtx_mongodb.unlock();
            return false;
        }
        if(!this->_db.has_collection("tasks")){
            cpp_utils::print_error("Knowledge base does not have a tasks collection");
            this->_mtx_mongodb.unlock();
            return false;
        }
        this->_collections.clear();
        this->_collections.insert(std::pair<std::string,mongocxx::collection>("environment",this->_db["environment"]));
        this->_collections.insert(std::pair<std::string,mongocxx::collection>("reference_frames",this->_db["reference_frames"]));
        this->_collections.insert(std::pair<std::string,mongocxx::collection>("parameters",this->_db["parameters"]));
        this->_collections.insert(std::pair<std::string,mongocxx::collection>("skills",this->_db["skills"]));
        this->_collections.insert(std::pair<std::string,mongocxx::collection>("tasks",this->_db["tasks"]));
    }catch(const mongocxx::operation_exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }
    this->_config_internal=config;
    this->_mtx_mongodb.unlock();
    return true;
}

bool KnowledgeBase::terminate(){
    return true;
}

bool KnowledgeBase::load_parameters(){

    unsigned max_tries=3;
    for(unsigned i=0;i<max_tries;i++){
        try{
            if(!this->_db.has_collection("parameters")){
                cpp_utils::print_warning("Knowledge base has no parameters collection");
                return false;
            }
            this->_mtx_mongodb.lock();
            if(this->_collections["parameters"].count_documents({bsoncxx::builder::stream::document{}<<"type"<<"control"<<bsoncxx::builder::stream::finalize})!=1){
                cpp_utils::print_error("No or multiple controller configuration files in knowledge base.");
                this->_mtx_mongodb.unlock();
                return false;
            }else{
                bsoncxx::stdx::optional<bsoncxx::document::value> doc=this->_collections["parameters"].find_one({bsoncxx::builder::stream::document{}<<"type"<<"control"<<bsoncxx::builder::stream::finalize});
                nlohmann::json config;
                std::string config_str=bsoncxx::to_json(*doc);
                config=nlohmann::json::parse(config_str);
                this->_local_memory.modify_config_cntr(config);
            }
            if(this->_collections["parameters"].count_documents({bsoncxx::builder::stream::document{}<<"type"<<"frames"<<bsoncxx::builder::stream::finalize})!=1){
                cpp_utils::print_error("No or multiple frames configuration files in knowledge base.");
                this->_mtx_mongodb.unlock();
                return false;
            }else{
                bsoncxx::stdx::optional<bsoncxx::document::value> doc=this->_collections["parameters"].find_one({bsoncxx::builder::stream::document{}<<"type"<<"frames"<<bsoncxx::builder::stream::finalize});
                nlohmann::json config;
                std::string config_str=bsoncxx::to_json(*doc);
                config=nlohmann::json::parse(config_str);
                this->_local_memory.modify_config_frames(config);
            }
            if(this->_collections["parameters"].count_documents({bsoncxx::builder::stream::document{}<<"type"<<"general"<<bsoncxx::builder::stream::finalize})!=1){
                cpp_utils::print_error("No or multiple general configuration files in knowledge base.");
                this->_mtx_mongodb.unlock();
                return false;
            }else{
                bsoncxx::stdx::optional<bsoncxx::document::value> doc=this->_collections["parameters"].find_one({bsoncxx::builder::stream::document{}<<"type"<<"general"<<bsoncxx::builder::stream::finalize});
                nlohmann::json config;
                std::string config_str=bsoncxx::to_json(*doc);
                config=nlohmann::json::parse(config_str);
                this->_local_memory.modify_config_general(config);
            }
            if(this->_collections["parameters"].count_documents({bsoncxx::builder::stream::document{}<<"type"<<"user"<<bsoncxx::builder::stream::finalize})!=1){
                cpp_utils::print_error("No or user configuration files in knowledge base.");
                this->_mtx_mongodb.unlock();
                return false;
            }else{
                bsoncxx::stdx::optional<bsoncxx::document::value> doc=this->_collections["parameters"].find_one({bsoncxx::builder::stream::document{}<<"type"<<"user"<<bsoncxx::builder::stream::finalize});
                nlohmann::json config;
                std::string config_str=bsoncxx::to_json(*doc);
                config=nlohmann::json::parse(config_str);
                this->_local_memory.modify_config_user(config);
            }
            if(this->_collections["parameters"].count_documents({bsoncxx::builder::stream::document{}<<"type"<<"system"<<bsoncxx::builder::stream::finalize})!=1){
                cpp_utils::print_error("No or multiple system configuration files in knowledge base.");
                this->_mtx_mongodb.unlock();
                return false;
            }else{
                bsoncxx::stdx::optional<bsoncxx::document::value> doc=this->_collections["parameters"].find_one({bsoncxx::builder::stream::document{}<<"type"<<"system"<<bsoncxx::builder::stream::finalize});
                nlohmann::json config;
                std::string config_str=bsoncxx::to_json(*doc);
                config=nlohmann::json::parse(config_str);
                this->_local_memory.modify_config_system(config);
            }
            this->_mtx_mongodb.unlock();
            return true;
        }catch(const mongocxx::logic_error& e){
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }catch(const mongocxx::operation_exception& e){
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }catch(const mongocxx::exception& e){
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }catch(const bsoncxx::exception& e){
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }
    }
    return false;
}

bool KnowledgeBase::load_document(const std::string &id, const std::string &type, nlohmann::json& descr){
    unsigned max_tries=3;
    for(unsigned i=0;i<max_tries;i++){
        try{
            this->_mtx_mongodb.lock();
            if(!this->_db.has_collection(type)){
                if(i<max_tries-1){
                    if(this->_client!=nullptr){
                        this->_client.reset();
                    }
                    this->initialize(this->_config_internal);
                    continue;
                }
                cpp_utils::print_error("Knowledge base has no "+type+" collection");
                this->_mtx_mongodb.unlock();
                return false;
            }
            unsigned n_doc = this->_collections[type].count_documents({bsoncxx::builder::stream::document{}<<"name"<<id<<bsoncxx::builder::stream::finalize});
            if(n_doc==0){
//                                            cpp_utils::print_error("No document with id "+id+" of type "+type+" present in knowledge base");
                descr="";
                this->_mtx_mongodb.unlock();
                return false;
            }
            if(n_doc>1){
                cpp_utils::print_error("Multiple documents with id "+id+" of type "+type+" present in knowledge base.");
                descr="";
                this->_mtx_mongodb.unlock();
                return false;
            }
            bsoncxx::stdx::optional<bsoncxx::document::value> doc = this->_collections[type].find_one({bsoncxx::builder::stream::document{}<<"name"<<id<<bsoncxx::builder::stream::finalize});
            std::string descr_str=bsoncxx::to_json(*doc);
            descr=nlohmann::json::parse(descr_str);
            this->_mtx_mongodb.unlock();
            return true;
        }catch(const mongocxx::logic_error& e){
            cpp_utils::print_error("Loading of document with name "+id+" of type "+type+ " has failed.");
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                if(this->_client!=nullptr){
                    this->_client.reset();;
                }
                this->initialize(this->_config_internal);
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }catch(const mongocxx::operation_exception& e){
            cpp_utils::print_error("Loading of document with name "+id+" of type "+type+ " has failed.");
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                if(this->_client!=nullptr){
                    this->_client.reset();;
                }
                this->initialize(this->_config_internal);
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }catch(const mongocxx::exception& e){
            cpp_utils::print_error("Loading of document with name "+id+" of type "+type+ " has failed.");
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                if(this->_client!=nullptr){
                    this->_client.reset();;
                }
                this->initialize(this->_config_internal);
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }catch(const bsoncxx::exception& e){
            cpp_utils::print_error("Loading of document with name "+id+" of type "+type+ " has failed.");
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                if(this->_client!=nullptr){
                    this->_client.reset();;
                }
                this->initialize(this->_config_internal);
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }catch(const nlohmann::detail::parse_error& e){
            cpp_utils::print_error("Loading of document with name "+id+" of type "+type+ " has failed.");
            std::cout<<e.what()<<std::endl;
            if(i<max_tries-1){
                continue;
            }else{
                this->_mtx_mongodb.unlock();
                return false;
            }
        }
    }
    this->_mtx_mongodb.unlock();
    return false;
}

bool KnowledgeBase::load_task(const std::string &t, nlohmann::json& descr){
    return this->load_document(t,"tasks",descr);
}

bool KnowledgeBase::load_skill(const std::string& s, nlohmann::json& descr){
    return this->load_document(s,"skills",descr);
}

bool KnowledgeBase::load_object(const std::string& o, nlohmann::json &descr){
    return this->load_document(o,"environment",descr);
}

bool KnowledgeBase::load_object(const std::string &o, Object& obj){
    nlohmann::json obj_json;
    if(!this->load_object(o,obj_json)){
        return false;
    }
    obj.from_json(obj_json);
    return true;
}

bool KnowledgeBase::load_reference_frame(const std::string& f, nlohmann::json &descr){
    return this->load_document(f,"reference_frames",descr);
}

bool KnowledgeBase::load_reference_frame(const std::string &f, ReferenceFrame& frame){
    nlohmann::json frame_json;
    if(!this->load_reference_frame(f,frame_json)){
        return false;
    }
    frame.from_json(frame_json);
    return true;
}

bool KnowledgeBase::update_object(const std::string& id, const nlohmann::json &obj){

    nlohmann::json obj_kb;
    if(!this->load_object(id,obj_kb)){
        cpp_utils::print_error("Object with name "+id+" does not exist in knowledge base.");
        return false;
    }
    if(cpp_utils::find_json_value(obj,"q_o"))   obj_kb["q_o"]=obj["q_o"];
    if(cpp_utils::find_json_value(obj,"O_T_o"))   obj_kb["O_T_o"]=obj["O_T_o"];
    if(cpp_utils::find_json_value(obj,"EE_ob_com"))   obj_kb["EE_ob_com"]=obj["EE_ob_com"];
    if(cpp_utils::find_json_value(obj,"ob_I"))   obj_kb["ob_I"]=obj["ob_I"];
    if(cpp_utils::find_json_value(obj,"mass"))   obj_kb["mass"]=obj["mass"];
    if(cpp_utils::find_json_value(obj,"grasp_width"))   obj_kb["grasp_width"]=obj["grasp_width"];
    if(cpp_utils::find_json_value(obj,"geometry")){
        for(nlohmann::json::const_iterator itr = obj["geometry"].begin();itr != obj["geometry"].end();itr++){
            if(!cpp_utils::find_json_value(obj_kb,"geometry")){
                cpp_utils::print_error("Knowledge base inconsistency. Object "+itr.key()+" has no geometry property.");
                return false;
            }
            if(!cpp_utils::overwrite_valid_json(obj["geometry"][itr.key()],obj_kb["geometry"][itr.key()])){
                std::cout<<"BLA"<<std::endl;
                return false;
            }
        }
    }
    obj_kb["geometry"]=obj["geometry"];
    try{
        std::string obj_str=obj_kb.dump();
        bsoncxx::document::view_or_value doc=bsoncxx::from_json(obj_str);
        std::string id_str;
        cpp_utils::read_json_param(obj_kb,"name",id_str);
        this->_mtx_mongodb.lock();
        this->_db["environment"].replace_one(bsoncxx::builder::stream::document{} << "name" << id_str << bsoncxx::builder::stream::finalize,doc);
        this->_mtx_mongodb.unlock();
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }
    return true;
}

bool KnowledgeBase::update_reference_frame(const std::string& id, const nlohmann::json &frame){

    nlohmann::json frame_kb;
    if(!this->load_reference_frame(id,frame_kb)){
        cpp_utils::print_error("Reference frame with id "+id+" does not exist in knowledge base.");
        return false;
    }
    if(cpp_utils::find_json_value(frame,"O_T_f"))   frame_kb["O_T_f"]=frame["O_T_f"];
    //    if(cpp_utils::find_json_value(frame,"objects")){
    //        for(nlohmann::json::const_iterator itr = frame["objects"].begin();itr != frame["objects"].end();itr++){
    ////            if(!cpp_utils::find_json_value(frame["objects"],itr.key()) || cpp_utils::find_json_value(frame["objects"],itr.key())){
    ////                return false;
    ////            }
    //            if(!cpp_utils::overwrite_valid_json(frame["objects"][itr.key()],frame_kb["objects"][itr.key()])){
    //                return false;
    //            }
    //        }
    //    }
    frame_kb["objects"]=frame["objects"];
    try{
        std::string frame_str=frame_kb.dump();
        bsoncxx::document::view_or_value doc=bsoncxx::from_json(frame_str);
        std::string id_str;
        cpp_utils::read_json_param(frame_kb,"name",id_str);
        this->_mtx_mongodb.lock();
        this->_db["reference_frames"].replace_one(bsoncxx::builder::stream::document{} << "name" << id_str << bsoncxx::builder::stream::finalize,doc);
        this->_mtx_mongodb.unlock();
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }
    return true;
}

bool KnowledgeBase::insert_object(const std::string& id, const nlohmann::json& obj){
    try{
        nlohmann::json obj_test;
        if(this->load_object(id,obj_test)){
            cpp_utils::print_error("Object with id "+id+" already exists in knowledge base. Can not insert second object with same id.");
            return false;
        }
        std::string obj_str=obj.dump();
        bsoncxx::document::view_or_value doc=bsoncxx::from_json(obj_str);
        this->_mtx_mongodb.lock();
        this->_db["environment"].insert_one(doc);
        this->_mtx_mongodb.unlock();
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }
    return true;
}

bool KnowledgeBase::insert_reference_frame(const std::string& id, const nlohmann::json& frame){
    try{
        nlohmann::json frame_test;
        if(this->load_reference_frame(id,frame_test)){
            cpp_utils::print_error("Reference frame with id "+id+" already exists in knowledge base. Can not insert second reference frame with same id.");
            return false;
        }
        std::string frame_str=frame.dump();
        bsoncxx::document::view_or_value doc=bsoncxx::from_json(frame_str);
        this->_mtx_mongodb.lock();
        this->_db["reference_frames"].insert_one(doc);
        this->_mtx_mongodb.unlock();
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }
    return true;
}

bool KnowledgeBase::teach_object(const std::string &object, const Percept& p, bool is_reference, const std::string &reference_frame, bool teach_width){
    if(is_reference && reference_frame!="none"){
        cpp_utils::print_error("Object cannot be reference frame and be referenced to a reference frame at the same time.");
        return false;
    }
    nlohmann::json obj_json;
    Object o;
    double grasp_width=0;
    if(teach_width){
        grasp_width=p.gripper_width;
    }
    Eigen::Matrix<double,4,4> O_T_o_EE=p.O_T_EE;
    if(!this->load_object(object,obj_json)){
        o.name=object;
        o.q_o=p.q;
        o.grasp_width=grasp_width;
        o.O_T_o=this->transform_to_F(O_T_o_EE);
        if(!this->insert_object(object,o.to_json())){
            cpp_utils::print_error("Could not insert new object with name "+object+" into knowledge base.");
            return false;
        }
        cpp_utils::print_success("Inserted new object with name "+object+" into knowledge base.");
    }else{
        o.from_json(obj_json);
        o.q_o=p.q;
        if(!teach_width){
            grasp_width=o.grasp_width;
        }
        o.grasp_width=grasp_width;
        o.O_T_o=this->transform_to_F(O_T_o_EE);
        this->update_object(object,o.to_json());
        cpp_utils::print_success("Assigned new pose to object with id "+object+".");
    }

    ReferenceFrame frame;
    std::string id_ref;
    if(is_reference || reference_frame!="none"){
        if(reference_frame!="none"){
            id_ref=reference_frame;
        }else{
            id_ref=object;
        }
        if(!this->load_reference_frame(id_ref,frame)){
            if(reference_frame!="none"){
                cpp_utils::print_error("No reference frame with id "+id_ref+" exists in knowledge base.");
                return false;
            }
            frame.name=id_ref;
            frame.O_T_f=this->transform_to_F(O_T_o_EE);
            if(!this->insert_reference_frame(id_ref,frame.to_json())){
                cpp_utils::print_error("Could not insert new reference frame with id "+id_ref+" into knowledge base.");
                return false;
            }
            cpp_utils::print_success("Inserted new reference frame with id "+id_ref+" into knowledge base.");
        }else if(reference_frame!="none"){
            nlohmann::json R_T_o_json;
            Eigen::Matrix<double,4,4> R_T_o=cpp_utils::invert_transformation_matrix(frame.O_T_f)*o.O_T_o;
            cpp_utils::write_json_array<double,4,4>(R_T_o_json,R_T_o);
            frame.objects[object]=R_T_o_json;
            this->update_reference_frame(id_ref,frame.to_json());
            cpp_utils::print_success("Connected object with id "+ object +" to reference frame with id "+id_ref+".");
        }else if(is_reference){
            frame.O_T_f=this->transform_to_F(O_T_o_EE);
            this->update_reference_frame(id_ref,frame.to_json());
            cpp_utils::print_success("Modified reference frame with id "+id_ref+".");
        }
    }
    return true;
}

bool KnowledgeBase::teach_object(const std::string& object, const Eigen::Matrix<double,4,4>& O_T_EE, const Eigen::Matrix<double,7,1>& q){
    nlohmann::json obj_json;
    Object o;
    Eigen::Matrix<double,4,4> O_T_o_EE=O_T_EE;
    if(!this->load_object(object,obj_json)){
        o.name=object;
        o.q_o=q;
        o.O_T_o=this->transform_to_F(O_T_o_EE);
        if(!this->insert_object(object,o.to_json())){
            cpp_utils::print_error("Could not insert new object with name "+object+" into knowledge base.");
            return false;
        }
        cpp_utils::print_success("Inserted new object with name "+object+" into knowledge base.");
        return true;
    }
    o.from_json(obj_json);
    o.q_o=q;
    o.O_T_o=this->transform_to_F(O_T_o_EE);
    Eigen::Matrix<double,4,4> F_T_TCP = cpp_utils::rotate_matrix(this->get_local_memory()->access_config_frames().EE_T_TCP,this->get_local_memory()->access_config_frames().F_T_EE);
    this->update_object(object,o.to_json());
    cpp_utils::print_success("Assigned new pose to object with name "+object+".");
    return true;
}

bool KnowledgeBase::apply_reference_frame(const std::string& id){
    ReferenceFrame frame;
    if(!this->load_reference_frame(id,frame)){
        cpp_utils::print_error("No reference frame with id "+id+" exists in knowledge base.");
        return false;
    }
    for(nlohmann::json::const_iterator itr = frame.objects.begin();itr != frame.objects.end();itr++){
        Eigen::Matrix<double,4,4> R_T_o;
        cpp_utils::read_json_param<double,4,4>(frame.objects,itr.key(),R_T_o);
        Object obj;
        if(!this->load_object(itr.key(),obj)){
            cpp_utils::print_error("No object with id "+id+" exists in knowledge base.");
            return false;
        }else{
            obj.O_T_o=frame.O_T_f*R_T_o;
            if(!this->update_object(itr.key(),obj.to_json())){
                return false;
            }
        }
    }
    return true;
}

bool KnowledgeBase::db_convert_value(double& v,const std::string& id, const bsoncxx::document::view &doc) const{
    try{
        bsoncxx::document::element e = doc[id];
        v=e.get_double().value;
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
}

bool KnowledgeBase::db_convert_value(bool& v,const std::string& id, const bsoncxx::document::view &doc) const{
    try{
        bsoncxx::document::element e = doc[id];
        v=e.get_bool().value;
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
}

bool KnowledgeBase::db_convert_value(int &v, const std::string& id, const bsoncxx::document::view &doc) const{
    try{
        bsoncxx::document::element e = doc[id];
        v=e.get_int64().value;
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
}

bool KnowledgeBase::db_convert_value(std::string& v, const std::string &id, const bsoncxx::document::view &doc) const{
    try{
        bsoncxx::document::element e = doc[id];
        v=e.get_utf8().value.to_string();
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
}

Eigen::Matrix<double,4,4> KnowledgeBase::transform_to_F(const Eigen::Matrix<double, 4, 4>& O_T_EE){
    Eigen::Matrix<double,4,4> EE_T_O = cpp_utils::invert_transformation_matrix(O_T_EE);
    Eigen::Matrix<double,4,4> F_T_TCP = cpp_utils::rotate_matrix(this->get_local_memory()->get_persistent_data()->EE_T_TCP,this->get_local_memory()->access_config_frames().F_T_EE);
    Eigen::Matrix<double,4,4> F_T_O = cpp_utils::rotate_matrix(EE_T_O,F_T_TCP);
    return cpp_utils::invert_transformation_matrix(F_T_O);
}

Eigen::Matrix<double,4,4> KnowledgeBase::transform_to_EE(const Eigen::Matrix<double, 4, 4>& O_T_F){
    Eigen::Matrix<double,4,4> F_T_TCP = cpp_utils::rotate_matrix(this->get_local_memory()->get_persistent_data()->EE_T_TCP,this->get_local_memory()->access_config_frames().F_T_EE);
    return cpp_utils::rotate_matrix(F_T_TCP,O_T_F);
}

bool KnowledgeBase::sync_task_with_primary(std::string t){
    nlohmann::json request;
    request["task"]=t;
    nlohmann::json response;
    //    if(!cpp_utils::rpc_call("http://"+this->get_local_memory()->access_config_system().ip_primary+":8390","download_task",request,response)){
    //        cpp_utils::print_error("Could not sync task "+t+" with primary.");
    //        return false;
    //    }
    return this->upload_task(response["task"]);
}

bool KnowledgeBase::upload_document(const std::string& name, const std::string& type, const nlohmann::json &descr){
    try{
        std::string task_str=descr.dump();
        bsoncxx::document::view_or_value doc=bsoncxx::from_json(task_str);
        this->_mtx_mongodb.lock();
        this->_db[type].replace_one(bsoncxx::builder::stream::document{} << "name" << name << bsoncxx::builder::stream::finalize,doc);
        this->_mtx_mongodb.unlock();
    }catch(const mongocxx::logic_error& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const mongocxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }catch(const bsoncxx::exception& e){
        std::cout<<e.what()<<std::endl;
        this->_mtx_mongodb.unlock();
        return false;
    }
    return true;
}

bool KnowledgeBase::upload_task(const nlohmann::json &descr){
    return this->upload_document(descr["name"],"tasks",descr);
}

bool KnowledgeBase::upload_skill(const nlohmann::json &descr){
    return this->upload_document(descr["name"],"skills",descr);
}

}

