#pragma once

#include <map>
#include <string>

#include <mongocxx/exception/logic_error.hpp>
#include <mongocxx/exception/operation_exception.hpp>
#include <mongocxx/client.hpp>
#include <mongocxx/instance.hpp>
#include <mongocxx/options/find.hpp>
#include <mongocxx/uri.hpp>
#include <mongocxx/collection.hpp>

#include <bsoncxx/exception/exception.hpp>

#include "knowledge_base/concepts.hpp"
#include "knowledge_base/local_memory.hpp"

#include "utils/exceptions.hpp"
#include "bsoncxx/builder/stream/document.hpp"

#include "cpp_utils/network.hpp"


namespace mios {

using bsoncxx::builder::basic::kvp;
//using bsoncxx::builder::basic::make_array;
//using bsoncxx::builder::basic::make_document;
class ParameterServer;

struct ConfigInternal{
    std::string path_executable;
    std::string grasped_object;
};

/**
 * The knowledge base class provides access to the mongodb database and keeps a local short term memory for fast access.
 */
class KnowledgeBase{
public:
    /**
     * Constructor.
     */
    KnowledgeBase();

    /**
     * Returns a pointer to the local memory.
     * @return Pointer to local memory.
     */
    LocalMemory * const get_local_memory();

    /**
     * Initializes the knowledge base i.e. connects to the mongodb database on localhost and checks whether all necessary collections exist.
     * @param[in] port Port of the mongodb database on localhost. Default value is 27017.
     * @param[in] config Internal config file.
     * @return True if initialization was successful, false otherwise.
     */
    bool initialize(const ConfigInternal& config, unsigned port=27017);

    bool terminate();

    /**
     * Loads all default global parameter and controller parameter from the mongodb database. These can be modified by the user and will be
     * overwritten by any values defined in task descriptions or instance parameters.
     * @return True if parameters are successfully loaded, false otherwise.
     */
    bool load_parameters();

    /**
     * Loads the specified task description from the database.
     * @param[in] t Type id of the task.
     * @param[out] descr The task description will be written into a json struct.
     * @return True if task description was successfully loaded, false otherwise.
     */
    bool load_task(const std::string& t, nlohmann::json &descr);
//    bool load_task_parameters(const std::string t,std::string &descr);

    /**
     * Loads the specified skill description from the database.
     * @param[in] s Type id of the task.
     * @param[out] descr The skill description will be written into a json struct.
     * @return True if skill description was successfully loaded, false otherwise.
     */
    bool load_skill(const std::string &s, nlohmann::json &descr);

    /**
     * Loads the specified object description from the database.
     * @param[in] o Object id in database.
     * @param[out] descr The object description will be written into a json struct.
     * @return True if object description was successfully loaded, false otherwise.
     */
    bool load_object(const std::string& o, nlohmann::json &descr);

    /**
     * Loads the specified object description from the database.
     * @param[in] o Object id in database.
     * @param[out] obj The object description will be written into an object class object.
     * @return True if object description was successfully loaded, false otherwise.
     */
    bool load_object(const std::string& o, Object &obj);

    /**
     * Loads the specified reference frame from the database.
     * @param[in] o Reference frame id in database.
     * @param[out] frame The reference frame will be written into a reference frame class object.
     * @return True if reference frame was successfully loaded, false otherwise.
     */
    bool load_reference_frame(const std::string &f, nlohmann::json &descr);

    /**
     * Loads the specified reference frame from the database.
     * @param[in] o Reference frame id in database.
     * @param[out] frame The reference frame description will be written into a json struct.
     * @return True if reference frame was successfully loaded, false otherwise.
     */
    bool load_reference_frame(const std::string& f, ReferenceFrame &frame);

    /**
     * Updates the specified object in the database with user-defined values.
     * @param id Object id.
     * @param obj Object properties in json format.
     * @return True if update was successful, false otherwise.
     */
    bool update_object(const std::string &id, const nlohmann::json& obj);

    /**
     * Updates the specified reference frame in the database with user-defined values.
     * @param id Reference frame id.
     * @param obj Reference frame properties in json format.
     * @return True if update was successful, false otherwise.
     */
    bool update_reference_frame(const std::string &id, const nlohmann::json& frame);

    /**
     * Inserts a new object into the knowledge base.
     * @param id Object id of the new object.
     * @param obj Object description of the new object.
     * @return True if insertion was successful, false otherwise.
     */
    bool insert_object(const std::string& id, const nlohmann::json &obj);

    /**
     * Inserts a new reference frame into the knowledge base.
     * @param id Object id of the object connected to the reference frame.
     * @param frame Reference frame relative to origin frame.
     * @return True if insertion was successful, false otherwise.
     */
    bool insert_reference_frame(const std::string &id, const nlohmann::json &frame);

    /**
     * Saves the Cartesian and joint pose of the specified object. Note that the Cartesian pose is internally saved with respect to the flange.
     * When it is loaded from the knowledge base the current F_T_EE transformation is appplied.
     * @param id Object id.
     * @param p Percept struct.
     * @return True if teaching was successful, false otherwise.
     */
    bool teach_object(const std::string& object, const Percept &p, bool is_reference=false, const std::string& reference_frame="none", bool teach_width=false);

    /**
     * Saves the specified Cartesian and joint poses of the specified object. Note that the Cartesian pose is internally saved with respect to the flange.
     * When it is loaded from the knowledge base the current F_T_EE transformation is appplied.
     * @param id Object id.
     * @param p Percept struct.
     * @return True if teaching was successful, false otherwise.
     */
    bool teach_object(const std::string &object, const Eigen::Matrix<double,4,4>& O_T_EE, const Eigen::Matrix<double,7,1>& q);

    /**
     * Applies the reference frame with the specified id to its connected objects.
     * @param id Reference frame id.
     * @return True if application was successful, false otherwise.
     */
    bool apply_reference_frame(const std::string& id);

    template<typename T>
    void set_parameter(const std::string& p,const std::string& c, T v){
        this->_collections["parameters"].update_one(bsoncxx::builder::stream::document{} << "type"<<c<<bsoncxx::builder::stream::finalize,
                                                    bsoncxx::builder::stream::document{} << "$set" << bsoncxx::builder::stream::open_document <<
                                                    p << v << bsoncxx::builder::stream::close_document << bsoncxx::builder::stream::finalize);
    }

    template<std::size_t S1,std::size_t S2>
    void set_parameter(const std::string& p,const std::string& c,Eigen::Matrix<double,S1,S2> v){
        this->_collections["parameters"].update_one(bsoncxx::builder::stream::document{} << "type"<<c<<bsoncxx::builder::stream::finalize,
                                                    bsoncxx::builder::stream::document{} << "$set" << bsoncxx::builder::stream::open_document <<
                                                    p << v << bsoncxx::builder::stream::close_document << bsoncxx::builder::stream::finalize);
    }

    /**
     * Transforms a given end effector pose (in origin frame) into a flange pose.
     * @param O_T_EE End effector pose in origin frame.
     * @return Flange pose in origin frame.
     */
    Eigen::Matrix<double,4,4> transform_to_F(const Eigen::Matrix<double,4,4>& O_T_EE);

    /**
     * Transforms a given flange pose (in origin frame) into an end effector pose.
     * @param O_T_F Flange pose in origin frame.
     * @return End effector pose in origin frame.
     */
    Eigen::Matrix<double,4,4> transform_to_EE(const Eigen::Matrix<double,4,4>& O_T_F);

    void set_live_parameter_server(std::shared_ptr<ParameterServer> server);

    bool sync_task_with_primary(std::string t);
    bool sync_skill_with_primary(std::string s);
    bool sync_concept_with_primary(std::string c);

    nlohmann::json get_live_parameter(const std::string& parameter) const;

    std::string get_event(const std::string &e) const;
    void set_event(const std::string& e, const std::string& state);

private:

    bool upload_task(const nlohmann::json& descr);
    bool upload_skill(const nlohmann::json& descr);
    bool upload_concept(const nlohmann::json& descr);

    bool load_document(const std::string& id, const std::string& type, nlohmann::json& descr);
    bool upload_document(const std::string& name, const std::string& type, const nlohmann::json& descr);

    template<std::size_t S1,std::size_t S2>bool load_parameter(Eigen::Matrix<double,S1,S2>& m, const std::string& id, const bsoncxx::document::view &doc) const{
        if(doc.find(id)==doc.end()){
            cpp_utils::print_error("Could not load parameter "+id+".");
            throw ParameterLoadException();
        }else{
            if(!this->db_convert_matrix<S1,S2>(m,id,doc)){
                cpp_utils::print_error("Could not load parameter "+id+".");
                throw ParameterLoadException();
            }
        }
    }

    template<std::size_t S1,std::size_t S2>void load_parameter(Eigen::Matrix<int,S1,S2>& m, const std::string& id, const bsoncxx::document::view &doc) const{
        if(doc.find(id)==doc.end()){
            cpp_utils::print_error("Could not load parameter "+id+".");
            throw ParameterLoadException();
        }else{
            if(!this->db_convert_matrix<S1,S2>(m,id,doc)){
                cpp_utils::print_error("Could not load parameter "+id+".");
                throw ParameterLoadException();
            }
        }
    }

    template<typename T>void load_parameter(T& v, const std::string& id, const bsoncxx::document::view &doc) const{
        if(doc.find(id)==doc.end()){
                cpp_utils::print_error("Could not load parameter "+id+".");
                throw ParameterLoadException();
        }else{
            if(!this->db_convert_value(v,id,doc)){
                cpp_utils::print_error("Could not load parameter "+id+".");
                throw ParameterLoadException();
            }
        }
    }

    template<size_t S1,size_t S2>bool db_convert_matrix(Eigen::Matrix<double,S1,S2>& m, const std::string& id, const bsoncxx::document::view &doc) const{

        try{
            bsoncxx::document::element e = doc[id];
            for(unsigned i=0;i<m.cols();i++){
                for(unsigned j=0;j<m.rows();j++){
                    m(j,i)=e.get_array().value[i*m.rows()+j].get_double().value;
                }
            }
        }catch(mongocxx::logic_error& e){
            std::cout<<e.what()<<std::endl;
        }catch(const bsoncxx::exception& e){
            std::cout<<e.what()<<std::endl;
            return false;
        }
        return true;
    }

    template<size_t S1,size_t S2>
    bool db_convert_matrix(Eigen::Matrix<int,S1,S2>& m, const std::string& id, const bsoncxx::document::view &doc) const{

        try{
            bsoncxx::document::element e = doc[id];
            for(unsigned i=0;i<m.cols();i++){
                for(unsigned j=0;j<m.rows();j++){
                    m(j,i)=e.get_array().value[i*m.rows()+j].get_int32().value;
                }
            }
        }catch(mongocxx::logic_error& e){
            std::cout<<e.what()<<std::endl;
        }catch(const bsoncxx::exception& e){
            std::cout<<e.what()<<std::endl;
            return false;
        }
        return true;
    }

    bool db_convert_value(double& v,const std::string& id, const bsoncxx::document::view &doc) const;
    bool db_convert_value(bool& v,const std::string& id, const bsoncxx::document::view &doc) const;
    bool db_convert_value(int &v, const std::string& id, const bsoncxx::document::view &doc) const;
    bool db_convert_value(std::string& v,const std::string& id, const bsoncxx::document::view &doc) const;

    mongocxx::instance _mongo_inst;
    std::unique_ptr<mongocxx::client> _client;
    mongocxx::database _db;

    std::map<std::string,mongocxx::collection> _collections;

    ConfigInternal _config_internal;
    LocalMemory _local_memory;

    std::map<std::string,std::string> _event_memory;

    std::shared_ptr<ParameterServer> _live_parameters;

    std::mutex _mtx_mongodb;
};

}
