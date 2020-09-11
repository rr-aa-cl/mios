#include "tasks/extract_object.hpp"

#include "skills/move_to_pose_cart.hpp"
#include "skills/extraction.hpp"
#include "msrm_utils/json.hpp"
#include "msrm_utils/math.hpp"

namespace mios{

ExtractObject::ExtractObject(Core *core):Task("ExtractObject",core){
}

void ExtractObject::initialize_context(){
    reserve_skill("extraction");
}

void ExtractObject::execute(){
    Percept p;
    if(!get_percept(p,{})){
        spdlog::error("Could not acquire current percept.");
        return;
    }
    if(!p.proprioception.is_grasping || m_memory->get_live_context()->grasped_object->name!=m_extractable){
        spdlog::error("I have not grasped an object or the grasped object is not the extractable");
        return;
    }
    overwrite_context("extraction","control","control_mode",0);

    write_skill_object("extraction","Extractable",m_extractable);
    write_skill_object("extraction","ExtractFrom",m_extract_from);
    write_skill_object("extraction","ExtractTo",m_extract_to);

    execute_skill<Extraction,SkillParametersExtraction>("extraction");
}

bool ExtractObject::read_parameters(const nlohmann::json& params){
    if(!msrm_utils::read_json_param(params,"extractable",m_extractable)){
        spdlog::error("Missing parameter: extractable");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"extract_from",m_extract_from)){
        spdlog::error("Missing parameter: extract_from");
        return false;
    }
    if(!msrm_utils::read_json_param(params,"extract_to",m_extract_to)){
        spdlog::error("Missing parameter: extract_to");
        return false;
    }
    return true;
}

void ExtractObject::get_default_context(nlohmann::json &context){
    context["parameters"] = nlohmann::json();
    context["parameters"]["extractable"]=nlohmann::json();
    context["parameters"]["extract_from"]=nlohmann::json();
    context["parameters"]["extract_to"]=nlohmann::json();

    context["skills"]["extraction"]=nlohmann::json();
    context["skills"]["extraction"]["control"]={{"control_mode",0}};
    context["skills"]["extraction"]["skill"].update({{"traj_speed",{0.05,0.2}}});
    context["skills"]["extraction"]["skill"].update({{"traj_acc",{0.5,1}}});
    context["skills"]["extraction"]["skill"].update({{"stuck_dx_thr",0.01}});
    context["skills"]["extraction"]["skill"].update({{"search_a",{5,5,0,0,0,0}}});
    context["skills"]["extraction"]["skill"].update({{"search_f",{0.5,0.5,0,0,0,0}}});
    context["skills"]["extraction"]["type"]="Extraction";
}

}
