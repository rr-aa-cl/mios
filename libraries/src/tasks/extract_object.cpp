#include "tasks/extract_object.hpp"

#include "skills/move_to_pose_joint.hpp"
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
void ExtractObject::evaluate(){
    write_result(get_result().skill_results["extraction"].success,get_result().skill_results["extraction"].cost_suc,get_result().skill_results["extraction"].cost_err,get_result().skill_results["extraction"].results);
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

}
