import os
import json


def create_skill(description: dict):
    path_header = os.getcwd() + '/../../libraries/include/skills/'
    path_src = os.getcwd() + '/../../libraries/src/skills/'
    path_context = os.getcwd() + '/../../libraries/contexts/skills/'

    file_name = description["file_name"]
    name = description["name"]
    parameters = description["parameters"]
    if len(name) == 0:
        print("Class name has no letters.")
        return False
    if name[0].isupper() is False:
        print("Class name must begin with capital letter.")
        return False
    if name.isalpha() is False:
        print("Class name must only consist of letters.")
        return False

    if os.path.exists(path_header + file_name + '.hpp') is True:
        print('A header file ' + file_name + '.hpp already exists.')
        return False

    if os.path.exists(path_src + file_name + '.cpp') is True:
        print('A source file ' + file_name + '.cpp already exists.')
        return False

    if os.path.exists(path_context + name + '.json') is True:
        print('A context file ' + name + '.json already exists.')
        return False

    if not os.path.isdir(path_header):
        os.makedirs(path_header)

    if not os.path.isdir(path_src):
        os.makedirs(path_src)

    if not os.path.isdir(path_context):
        os.makedirs(path_context)

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
        elif type(par[1]) is float:
            par_type = "double"
        elif type(par[1]) is int:
            par_type = "int"
        elif type(par[1]) is str:
            par_type = "std::string"
        elif type(par[1]) is list:
            par_size = str(len(par[1]))
            if type(par[1][0]) is bool:
                par_type = "Eigen::Matrix<bool," + par_size + ",1>"
            elif type(par[1][0]) is float:
                par_type = "Eigen::Matrix<double," + par_size + ",1>"
            elif type(par[1][0]) is int:
                par_type = "Eigen::Matrix<int," + par_size + ",1>"
            elif type(par[1][0]) is str:
                par_type = "Eigen::Matrix<std::string," + par_size + ",1>"
            else:
                print("Invalid type for elements of array parameter " + par[0])
                return False
        else:
            print("Invalid type for parameter " + par[0])
            return False

        file_header.write(par_type + " " + par[0] + ";\n")

    file_header.write("};\n"
                      "\n")

    file_header.write("class " + name + " : public Skill{\n"
                                        "public:\n" +
                      name + "(const std::string& name,Memory* memory, Portal* portal, const Percept& p);\n")
    file_header.write("void evaluate(); override\n")
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
    file_src.write(name + "::" + name + "(const std::string& name, Memory* memory, Portal* portal, const Percept& p):Skill"
                                        '("' + name + '",{' + objects + "},name,memory,portal,p){}\n")

    file_src.write("std::shared_ptr<ManipulationPrimitive> " + name + "::get_initial_mp(const Percept& p){}\n")
    file_src.write("void " + name + "::evaluate(){}\n")
    file_src.write("}\n")

    context = dict()
    context["name"] = name
    for par in parameters:
        context[par[0]] = par[1]

    with open(path_context + name + '.json', 'w') as file:
        json.dump(context, file)


def remove_skill(file_name: str, name: str):
    path_header = os.getcwd() + '/../../libraries/include/skills/'
    path_src = os.getcwd() + '/../../libraries/src/skills/'
    path_context = os.getcwd() + '/../../libraries/contexts/skills/'

    os.remove(path_header + file_name + ".hpp")
    os.remove(path_src + file_name + ".cpp")
    os.remove(path_context + name + ".json")
