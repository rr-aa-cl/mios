#pragma once

#include <eigen3/Eigen/Core>

#include "cpp_utils/json.hpp"
#include "cpp_utils/math.hpp"

namespace mios {

class Concept{
public:
    Concept(std::string id);
    ~Concept();

    std::string get_id();
    virtual nlohmann::json to_json();
    virtual void from_json(const nlohmann::json& p);

private:

    std::string id;

};

class Spatial : public virtual Concept{
public:
    Spatial(std::string id);
    ~Spatial();

    virtual nlohmann::json to_json();
    virtual void from_json(const nlohmann::json& p);

    const Eigen::Matrix<double,4,4>& get_O_T_S();
    Eigen::Matrix<double, 4, 4> get_TF_T_S(const Eigen::Matrix<double,3,3>& O_R_TF);
    const Eigen::Matrix<double,7,1>& get_q();

protected:

    Eigen::Matrix<double,4,4> O_T_S;
    Eigen::Matrix<double,7,1> q;
};

class Inertial : public virtual Concept{
public:
    Inertial(std::string id);
    ~Inertial();

    virtual nlohmann::json to_json();
    virtual void from_json(const nlohmann::json& p);

    double get_m();
    Eigen::Matrix<double,3,1> get_com();
    Eigen::Matrix<double,3,3> get_I();
protected:
    double m;
    Eigen::Matrix<double,3,1> com;
    Eigen::Matrix<double,3,3> I;
};

class Geometry : public virtual Concept{
public:
    Geometry(std::string id);
    ~Geometry();

    virtual nlohmann::json to_json();
    virtual void from_json(const nlohmann::json& p);
private:
    double width;
    double height;
    double depth;
};

class Location : public Spatial{
public:
    Location(std::string id);
    ~Location();

    nlohmann::json to_json();
    void from_json(const nlohmann::json &p);
private:
};

class PhysicalObject : public Geometry,public Inertial,public Spatial{
public:
    PhysicalObject(std::string id);
    ~PhysicalObject();

    nlohmann::json to_json();
    void from_json(const nlohmann::json &p);
private:
};

class Robot : public PhysicalObject{
public:
    Robot(std::string id);
    ~Robot();

    nlohmann::json to_json();
    void from_json(const nlohmann::json &p);

    void set_ip(const std::string& ip);
    void set_hostname(const std::string &hostname);

    std::string get_hostname();
    std::string get_ip();
private:
    std::string hostname;
    std::string ip;
};

/**
 * The object class is the internal representation of an object description. Object descriptions are saved in the mongodb databse.
 */
class Object{
public:
    /**
     * The constructor sets default values for the object properties.
     */
    Object();

    /**
      * Destructor.
      */
    ~Object();

    /**
     * Transforms the internal object representation into json format.
     * @return Object representation in json format.
     */
    nlohmann::json to_json();

    /**
     * Reads an object description from json format.
     * @param p Object description in json format.
     */
    void from_json(const nlohmann::json& p);

    /**
     * Transforms the object pose into the given task frame. Note, this is the flange pose.
     * @param O_R_TF Task frame.
     * @return Object pose in task frame
     */
    Eigen::Matrix<double,4,4> TF_T_o(const Eigen::Matrix<double,3,3>& O_R_TF);

    /**
     * The object id in both internal representation as well as the mongodb database.
     */
    std::string name;

    /**
     * The object pose in joint space.
     */
    Eigen::Matrix<double,7,1> q_o;

    /**
     * The Cartesian object pose in origin frame.
     */
    Eigen::Matrix<double,4,4> O_T_o;

    /**
     * Transformation matrix from EE frame to object frame.
     */
    Eigen::Matrix<double,4,4> EE_T_O;

    /**
     * The object's center of mass in EE frame.
     */
    Eigen::Matrix<double,3,1> EE_ob_com;

    /**
     * The object's intertial tensor in object frame.
     */
    Eigen::Matrix<double,3,3> ob_I;

    /**
     * The object's mass.
     */
    double mass;

    /**
     * Expected finger width when grasping the object.
     */
    double grasp_width;

    /**
     * The object's geometry description. It can have arbitrary properties that can be represented as scalars and arrays.
     */
    nlohmann::json geometry;
};

class ReferenceFrame{
public:
    /**
     * Constructor
     */
    ReferenceFrame();

    /**
     * Destructor
     */
    ~ReferenceFrame();

    /**
     * Returns the relative pose of the specified object with respect to the reference frame.
     * @param object Id of the object.
     * @return Relative frame of the object to the reference frame.
     */
    Eigen::Matrix<double,4,4> get_relative_pose(const std::string &object);

    /**
     * Transforms the internal object representation into json format.
     * @return Object representation in json format.
     */
    nlohmann::json to_json();

    /**
     * Reads an reference frame description from json format.
     * @param p Reference frame description in json format.
     */
    void from_json(const nlohmann::json& p);

    /**
     * The reference frame id in both internal representation as well as the mongodb database.
     */
    std::string name;

    /**
     * A map of relative frames for all objects connected to this reference frame.
     */
    nlohmann::json objects;

    /**
     * The reference frame relative to the origin frame.
     */
    Eigen::Matrix<double,4,4> O_T_f;
};

}
