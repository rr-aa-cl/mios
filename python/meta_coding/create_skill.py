import os


def create_skill(description: dict):
    path_header = os.getcwd() + '/../../libraries/include/skills/'
    path_src = os.getcwd() + '/../../libraries/src/skills/'

    file_name = description["file_name"]
    name = description["name"]
    parameters = description["parameters"]
    if len(name) == 0:
        print("Class name has no letters.")
        return
    if name[0].isupper() is False:
        print("Class name must begin with capital letter.")
        return
    if name.isalpha() is False:
        print("Class name must only consist of letters.")
        return

    if os.path.exists(path_header + file_name + '.hpp') is True:
        print('File ' + file_name + '.hpp already exists.')
        return

    if os.path.exists(path_src + file_name + '.cpp') is True:
        print('File ' + file_name + '.cpp already exists.')
        return

    file_header = open(path_header + file_name + '.hpp', 'w')
    file_src = open(path_src + file_name + '.cpp', 'w')

    file_header.write('#pragma once\n'
                     '\n'
                     '#include "skill/skill.hpp"\n')

    file_header.write('namespace mios{\n')

    file_header.write("class SkillParameters" + name + " : public SkillParameters{\n"
                                                       "public:\n")

    file_header.write("bool from_json(const nlohmann::json& parameters) override;\n")
    for par in parameters:
        if type(par[1]) is bool:
            par_type = "bool"
        if type(par[1]) is float:
            par_type = "double"
        if type(par[1]) is int:
            par_type = "int"
        if type(par[1]) is str:
            par_type = "std::string"
        if type(par[1]) is list:
            par_size = str(len(par[1]))
            if type(par[1][0]) is bool:
                par_type = "Eigen::Matrix<bool," + par_size + ",1>"
            if type(par[1][0]) is float:
                par_type = "Eigen::Matrix<double," + par_size + ",1>"
            if type(par[1][0]) is int:
                par_type = "Eigen::Matrix<int," + par_size + ",1>"
            if type(par[1][0]) is str:
                par_type = "Eigen::Matrix<std::string," + par_size + ",1>"

        file_header.write(par_type + " " + par[0] + ";\n")

    file_header.write("};\n"
                      "\n")

    file_header.write("class " + name + " : public Skill{\n"
                                        "public:\n" +
                                        name + "(const std::string& name,Memory* memory, const Percept& p);\n")
    file_header.write("void evaluate();\n")
    file_header.write("Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;\n")
    file_header.write("private:\n")
    file_header.write("std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;\n")
    file_header.write("bool check_local_suc_conditions(const Percept& p) override;\n")
    file_header.write("};\n")
    file_header.write("}\n")

    file_src.write("""#include "skills/""" + file_name + """.hpp"\n""")
    file_src.write("namespace mios{\n")
    file_src.write("bool SkillParameters" + name + "::from_json(const nlohmann::json& parameters){\n")
    file_src.write("}\n")
    objects = ""
    for o in description["objects"]:
        if o == description["objects"][-1]:
            objects += '"' + o + '"'
        else:
            objects += '"' + o + '",'
    file_src.write(name + "::" + name + "(const std::string& name, Memory* memory, const Percept& p):Skill"
                                        '("' + name + '",{' + objects + "},name,memory,p){}\n")

    file_src.write("std::shared_ptr<ManipulationPrimitive> " + name + "::get_initial_mp(const Percept& p){}\n")
    file_src.write("void " + name + "::evaluate(){}\n")
    file_src.write("}\n")


