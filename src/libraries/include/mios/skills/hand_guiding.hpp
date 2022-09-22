#pragma once
#include "mios/skill/skill.hpp"
#include <vector>
#include <array>

namespace mios{
class SkillParametersHandGuiding: public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,6,1> fix_dim;
    Eigen::Matrix<double,6,1> dist_walls;
    bool use_walls;
    bool record_trajectory;
    long recording_length;
    std::string recording_name;
    bool joint_mode;
};

class HandGuiding : public Skill{
public:
    HandGuiding(const std::string& id, Memory *memory, Portal *portal);
    ~HandGuiding();
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
private:
    bool check_local_suc_conditions(const Percept& p);
    void auxiliaries(const Percept &p) override;

    std::vector<std::array<double,16> > m_recording;
    std::vector<std::array<double,7> > m_recording_joint;
    
    long m_cnt_recording;

};
}
