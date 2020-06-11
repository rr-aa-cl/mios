import os


def create_strategy(description: dict):
    path_header = os.getcwd() + '/../../libraries/include/strategies/'
    path_src = os.getcwd() + '/../../libraries/src/strategies/'

    file_name = description["file_name"]
    name = description["name"]
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
                     '#include "strategy/primitive_strategy.hpp"\n')

    file_header.write('namespace mios{\n')

    file_header.write('class ' + name + ' : public PrimitiveStrategy{\n'
                                        'public:\n' +
                             'void initialize(const Percept& p_0) override;\n'
                             'void get_next_command(Actuator& cmd, const Percept& p) override;\n'
                             'void terminate(const Percept& p) override;\n'
                             'bool finished() override;\n'
                             '\n'
                             '};\n'
                             '}')

    file_src.write("""#include "strategies/""" + file_name + """.hpp"\n""")
    file_src.write("namespace mios{\n")
    file_src.write("void " + name + "::initialize(const Percept& p_0){}\n")
    file_src.write("void " + name + "::get_next_command(Actuator& cmd, const Percept& p_0){}\n")
    file_src.write("void " + name + "::terminate(const Percept& p){}\n")
    file_src.write("bool " + name + "::finished(){\n"
                                    "return false;\n"
                                    "}\n")
    file_src.write("}\n")


