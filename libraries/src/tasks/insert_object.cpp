#include "tasks/insert_object.hpp"

#include "skills/move_to_pose_joint.hpp"
#include "skills/move_to_pose_cart.hpp"
#include "skills/move_to_contact.hpp"
#include "skills/insertion.hpp"
#include "msrm_utils/json.hpp"
#include "msrm_utils/math.hpp"

namespace mios{

InsertObject::InsertObject(Core *core):Task("InsertObject",core){
}

void InsertObject::initialize_context(){
    reserve_skill("coarse_approach");
    reserve_skill("fine_approach");
    reserve_skill("contact");
    reserve_skill("insertion");
}

void InsertObject::execute(){
    Percept p;
    if(!get_percept(p,{})){
        spdlog::error("Could not acquire current percept.");
        write_error("TaskError");
        return;
    }
    if(!p.proprioception.is_grasping || m_memory->get_live_context()->grasped_object->name!=m_insertable){
        spdlog::error("I have not grasped an object or the grasped object is not the insertable");
        write_error("TaskError");
        return;
    }

    overwrite_context("coarse_approach","control","control_mode",3);
    overwrite_context("fine_approach","control","control_mode",2);
    overwrite_context("contact","control","control_mode",2);
    overwrite_context("insertion","control","control_mode",0);

    write_skill_object("coarse_approach","goal_pose",m_insert_approach);
    write_skill_object("fine_approach","goal_pose",m_insert_approach);
    write_skill_object("contact","goal_pose",m_insert_into);
    Eigen::Matrix<double,4,4> T_T_EE_g_offset;
    T_T_EE_g_offset.block<3,3>(0,0)=msrm_utils::eulerRPY_to_mat(m_offset(3),m_offset(4),m_offset(5));
    T_T_EE_g_offset.block<3,1>(0,3)=m_offset.block<3,1>(0,0);
    overwrite_context("fine_approach","skill","T_T_EE_g",msrm_utils::from_eigen<double,4,4>(m_memory->get_object(m_insert_approach)->O_T_OB));
    overwrite_context("fine_approach","skill","T_T_EE_g_offset",msrm_utils::from_eigen<double,4,4>(T_T_EE_g_offset));
    write_skill_object("insertion","Insertable",m_insertable);
    write_skill_object("insertion","InsertInto",m_insert_into);


    execute_skill<MoveToPoseJoint,SkillParametersMoveToPoseJoint>("coarse_approach");
    if(!get_result().skill_results["coarse_approach"].success){
        write_error("TaskError");
        return;
    }
    execute_skill<MoveToPoseCart,SkillParametersMoveToPoseCart>("fine_approach");
    if(!get_result().skill_results["fine_approach"].success){
        write_error("TaskError");
        return;
    }
    execute_skill<MoveToContact,SkillParametersMoveToContact>("contact");
    execute_skill<Insertion,SkillParametersInsertion>("insertion");
}

bool InsertObject::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"insertable",m_insertable)){
        spdlog::error("Missing parameter: insertable");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"insert_into",m_insert_into)){
        spdlog::error("Missing parameter: insert_into");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"insert_approach",m_insert_approach)){
        spdlog::error("Missing parameter: insert_approach");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(params,"offset",m_offset)){
        spdlog::error("Missing parameter: offset");
        return false;
    }
    return true;
}

void InsertObject::get_default_context(nlohmann::json &context){
    context["parameters"] = nlohmann::json();
    context["parameters"]["insertable"]=nlohmann::json();
    context["parameters"]["insert_into"]=nlohmann::json();
    context["parameters"]["insert_approach"]=nlohmann::json();
    context["parameters"]["offset"]={0,0,0,0,0,0};

    context["skills"]=nlohmann::json();
    context["skills"]["coarse_approach"]=nlohmann::json();
    context["skills"]["coarse_approach"]["control"]={{"control_mode",3}};
    context["skills"]["coarse_approach"]["skill"]={{"speed",0.5},{"acc",1}};
    context["skills"]["coarse_approach"]["type"]="MoveToPoseJoint";
    context["skills"]["fine_approach"]=nlohmann::json();
    context["skills"]["fine_approach"]["control"]={{"control_mode",2}};
    context["skills"]["fine_approach"]["skill"]={{"speed",{0.05,0.3}},{"acc",{0.5,1}}};
    context["skills"]["fine_approach"]["type"]="MoveToPoseCart";
    context["skills"]["contact"]=nlohmann::json();
    context["skills"]["contact"]["control"]={{"control_mode",2}};
    context["skills"]["contact"]["skill"]={{"speed",0.05}};
    context["skills"]["contact"]["type"]="MoveToContact";

    context["skills"]["insertion"]=nlohmann::json();
    context["skills"]["insertion"]["control"]={{"control_mode",0}};
    context["skills"]["insertion"]["skill"].update({{"traj_speed",{0.05,0.2}}});
    context["skills"]["insertion"]["skill"].update({{"traj_acc",{0.5,1}}});
    context["skills"]["insertion"]["skill"].update({{"stuck_dx_thr",0.01}});
    context["skills"]["insertion"]["skill"].update({{"search_a",{5,5,0,0,0,0}}});
    context["skills"]["insertion"]["skill"].update({{"search_f",{0.5,0.5,0,0,0,0}}});
    context["skills"]["insertion"]["skill"].update({{"ROI_x",{-1,1,-1,1,-1,1}}});
    context["skills"]["insertion"]["skill"].update({{"ROI_phi",{0,0,0,0,0,0}}});
    context["skills"]["insertion"]["type"]="Insertion";
}

}
