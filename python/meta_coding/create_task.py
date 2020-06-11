import os
from os import walk
import re


def create_task(description: dict):
    path_header = os.getcwd() + '/../../libraries/include/tasks/'
    path_src = os.getcwd() + '/../../libraries/src/tasks/'

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
                     '#include "task/task.hpp"\n')

    file_header.write('namespace mios{\n')

    file_header.write("class " + name + " : public Task{\n"
                                        "public:\n" +
                                        name + "(Core* core);\n")
    file_header.write("void evaluate() override;\n")
    file_header.write("void initialize_context() override;\n")
    file_header.write("void execute() override;\n")
    file_header.write("bool read_parameters(const nlohmann::json& params) override;\n")
    file_header.write("private:\n")
    file_header.write("};\n")
    file_header.write("}\n")

    file_src.write("""#include "tasks/""" + file_name + """.hpp"\n""")
    file_src.write("namespace mios{\n")
    file_src.write(name + "::" + name + "(Core* core):Task"
                                        '("' + name + '",core){}\n')

    file_src.write("void " + name + "::initialize_context(){}\n")
    file_src.write("void " + name + "::evaluate(){}\n")
    file_src.write("void " + name + "::execute(){}\n")
    file_src.write("bool " + name + "::read_parameters(const nlohmann::json& params){\n"
                                    "return true;\n"
                                    "}\n")
    file_src.write("}\n")


def refresh_task_factory():
    path_library_header = os.getcwd() + '/../../libraries/include/tasks/'
    path_library_src = os.getcwd() + '/../../libraries/src/tasks/'

    path_factory_header = os.getcwd() + '/../../task/include/task/'
    path_factory_src = os.getcwd() + '/../../task/src/'

    files = []
    for (dirpath, dirnames, filenames) in walk(path_library_header):
        files.extend(filenames)

    class_names = []
    for f in files:
        with open(path_library_header + f) as file:
            for num, line in enumerate(file, 1):
                m = re.search('class (.+?) :', line)
                if m:
                    class_names.append(m.group(1))
                else:
                    m = re.search('class (.+?):', line)
                    if m:
                        class_names.append(m.group(1))

    file_header = open(path_factory_header + "taskfactory" + '.hpp', 'w')
    file_src = open(path_factory_src + "taskfactory" + '.cpp', 'w')

    file_header.write("#pragma once\n")
    file_header.write("#include <memory>\n")
    file_header.write("\n")
    file_header.write("namespace mios{\n")
    file_header.write("class Task;\n")
    file_header.write("class Core;\n")

    file_header.write("enum TaskName{")
    task_names = ""
    for c in class_names:
        task_names += "TaskName" + c + ","
    task_names = task_names[:-1]
    file_header.write(task_names + "};\n")

    file_header.write("class TaskFactory{\n"
                      "public:\n"
                      "static TaskName get_task_name(const std::string& task);\n"
                      "static std::shared_ptr<Task> create_task(TaskName task, Core* core);\n"
                      "};\n")
    file_header.write("}\n")

    file_src.write('#include "task/taskfactory.hpp"\n')
    file_src.write('#include "task/task.hpp"\n')
    file_src.write('#include <msrm_utils/files.hpp>\n')
    file_src.write('#include <spdlog/spdlog.h>\n')
    for f in files:
        file_src.write('#include "tasks/' + f + '"\n')

    file_src.write("namespace mios{\n"
                   "\n")

    file_src.write("TaskName TaskFactory::get_task_name(const std::string& task){\n"
                   "switch(msrm_utils::str_to_int(task.c_str())){\n")
    for c in class_names:
        file_src.write('case msrm_utils::str_to_int("' + c + '"):\n'
                                                             'return TaskName' + c + ';\n')
    file_src.write("default:\n"
                   'spdlog::error("Task with id " + task + " does not exist.");\n'
                   'return TaskNameNullTask;\n')
    file_src.write("}\n"
                   "}\n"
                   "\n")

    file_src.write("std::shared_ptr<Task> TaskFactory::create_task(TaskName task, Core* core){\n"
                   "switch(task){\n")
    for c in class_names:
        file_src.write("case TaskName" + c + ":\n"
                                             "return std::make_shared<" + c + ">(core);\n")

    file_src.write("default:\n"
                   "return std::make_shared<NullTask>(core);\n"
                   "}\n")
    file_src.write("}\n"
                   "}\n")
