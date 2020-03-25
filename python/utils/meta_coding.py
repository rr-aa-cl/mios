from pymongo import MongoClient
import os


def create_task(task,host,overwrite=False):
    client_from = MongoClient('mongodb://' + host + ':27017')
    task_decr = client_from.mios.tasks.find_one({'name': task})
    if task_decr is None:
        print('No task description for task ' + task + ' found on host ' + host)
        return

    path_header = os.getcwd() + '/../../task/include/tasks/'
    path_src = os.getcwd() + '/../../task/src/tasks/'
    path_config = os.getcwd() + '/../../config/'

    if os.path.exists(path_header + task + '.hpp') is True:
        if overwrite is False:
            print('File ' + task + '.hpp already exists, aborting task creation.')
            return

    if os.path.exists(path_src + task + '.cpp') is True:
        if overwrite is False:
            print('File ' + task + '.cpp already exists, aborting task creation.')
            return

    with open(path_config + 'active_tasks') as f:
        tasks = f.read().splitlines()

    if task not in tasks:
        with open(path_config + 'active_tasks', 'a') as file:
            file.write(task + '\n')

    refresh_task_list()

    file_header = open(path_header + task+'.hpp', 'w')
    file_src = open(path_src + task + '.cpp', 'w')

    file_header.write('#pragma once\n'
                      '\n'
                      '#include "task/task.hpp"\n')

    file_header.write('namespace mios{\n')

    file_header.write('class ' + task + ' : public Task{\n'
                                        'public:\n' +
                      task + '();\n'
                                          'void initialize_task();\n'
                                          'void execute_task();\n'
                                          'const EvalTask& evaluate_task();\n')

    if 'parameters' in task_decr:
        file_header.write('bool read_parameters(const nlohmann::json& params);\n'
                          'private:\n')
        for key,val in task_decr["parameters"].items():
            if type(val) == str:
                file_header.write('std::string ' + key + ';\n')
            if type(val) == float or type(val) == int:
                file_header.write('double ' + key + ';\n')
            if type(val) == bool:
                file_header.write('bool ' + key + ';\n')
            if type(val) == list:
                if len(val) == 0:
                    pass
                else:
                    if type(val[0]) == str:
                        file_header.write('std::array<std::string,' + str(len(val)) + '> ' + key + ';\n')
                    if type(val[0]) == bool:
                        file_header.write('std::array<bool,' + str(len(val)) + '> ' + key + ';\n')
                    if type(val[0]) == float or type(val[0]) == int:
                        file_header.write('Eigen::Matrix<double,' + str(len(val)) + ',1> ' + key + ';\n')

    file_header.write('};\n'
                      '}\n')

    file_src.write('#include "tasks/' + task + '.hpp"\n')
    file_src.write('namespace mios{\n')

    file_src.write(task + '::' + task + '():Task("' + task + '"){\n'
                                        '}\n')
    file_src.write('void ' + task + '::initialize_task(){\n'
                                    '}\n')
    file_src.write('void ' + task + '::execute_task(){\n'
                                    '}\n')
    file_src.write('const EvalTask& ' + task + '::evaluate_task(){\n'
                                               'return this->_eval_task;\n'
                                    '}\n')

    if 'parameters' in task_decr:
        file_src.write('bool ' + task + '::read_parameters(const nlohmann::json& params){\n'
                                        'return true;\n'
                                                   '}\n')

    file_src.write('}\n')


def create_skill(skill,host,overwrite=False):
    client_from = MongoClient('mongodb://' + host + ':27017')
    skill_decr = client_from.mios.skills.find_one({'name':skill})
    if skill_decr is None:
        print('No skill description for skill ' + skill + ' found on host ' + host)
        return

    path_header = os.getcwd() + '/../../skill/include/skills/'
    path_src = os.getcwd() + '/../../skill/src/skills/'
    path_config = os.getcwd() + '/../../config/'

    if os.path.exists(path_header+skill + '.hpp') is True:
        if overwrite is False:
            print('File ' + skill + '.hpp already exists, aborting skill creation.')
            return

    if os.path.exists(path_src+skill + '.cpp') is True:
        if overwrite is False:
            print('File ' + skill + '.cpp already exists, aborting skill creation.')
            return

    with open(path_config+'active_skills') as f:
        skills = f.read().splitlines()

    if skill not in skills:
        with open(path_config+'active_skills', 'a') as file:
            file.write(skill + '\n')

    refresh_skill_header()

    file_header = open(path_header + skill + '.hpp', 'w')
    file_src = open(path_src + skill + '.cpp', 'w')

    file_header.write('#pragma once\n'
                      '#include "skill/skill.hpp"\n')
    file_header.write('namespace mios{\n')

    file_header.write('struct ConfigSkill_' + skill + ': public ConfigSkill{\n')
    for key,val in skill_decr.items():
        if type(val) == str:
            file_header.write('std::string ' + key + ';\n')
        if type(val) == float or type(val) == int:
            file_header.write('double ' + key + ';\n')
        if type(val) == bool:
            file_header.write('bool ' + key + ';\n')
        if type(val) == list:
            if len(val) == 0:
                pass
            else:
                if type(val[0]) == str:
                    file_header.write('std::array<std::string,' + str(len(val)) + '> ' + key + ';\n')
                if type(val[0]) == bool:
                    file_header.write('std::array<bool,' + str(len(val)) + '> ' + key + ';\n')
                if type(val[0]) == float or type(val[0]) == int:
                    file_header.write('Eigen::Matrix<double,' + str(len(val)) + ',1> ' + key + ';\n')

    file_header.write('};')

    file_header.write('class ' + skill + ' : public Skill{\n'
                                         'public:\n'
                                    + skill + '();\n'
                                    'void evaluate();\n'
                                    'bool read_skill_parameters(const nlohmann::json& p);\n'
                                    'private:\n'
                                    'void create_config();\n'
                                                  'void build_primitives(const Percept& p);\n'
                                                  'std::tuple<bool,std::string> check_edges(const Percept& p);\n'
                                                  'bool check_local_suc_conditions(const Percept& p);\n'
                                                  '};\n'
                                                  '}\n')

    file_src.write('#include "skills/' + skill + '.hpp"\n'
                                                 'namespace mios{\n')

    file_src.write(skill + '::' + skill + '():Skill("' + skill + '"){}\n')

    file_src.write('bool ' + skill + '::read_skill_parameters(const nlohmann::json& p){return false;}\n')

    file_src.write('void ' + skill + '::build_primitives(const Percept& p){}\n')
    file_src.write('std::tuple<bool,std::string> ' + skill + '::check_edges(const Percept& p){return std::tuple<bool,std::string>(false,"");}\n')
    file_src.write('bool ' + skill + '::check_local_suc_conditions(const Percept& p){return true;}\n')
    file_src.write('void ' + skill + '::evaluate(){}\n')
    file_src.write('void ' + skill + '::create_config(){\n'
                                     'this->_config=std::make_shared<ConfigSkill_' + skill + '>();\n'
                                     '}\n')

    file_src.write('}')


def refresh_task_list():
    path_header = os.getcwd() + '/../../task/include/task/'
    path_src = os.getcwd() + '/../../task/src/'
    path_config = os.getcwd() + '/../../config/'

    file_header = open(path_header + 'task_list.hpp', 'w')
    file_src = open(path_src + 'task_list.cpp', 'w')

    with open(path_config+'active_tasks') as f:
        tasks = f.read().splitlines()

    file_header.write('#pragma once\n'
                      '\n'
                      '#include "task/task.hpp"\n')

    file_src.write('#include "task/task_list.hpp"\n')
    file_src.write('namespace mios{\n')

    file_src.write('TaskList::TaskList(){\n')
    for t in tasks:
        file_header.write('#include "tasks/'+t+'.hpp"\n')
        file_src.write('this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("' + t + '",std::make_shared<' + t + '>()));\n')

    file_src.write('}\n'
                   '}\n')

    file_header.write('namespace mios{\n')

    file_header.write('struct TaskList{\n'
                      'TaskList();\n'
                      'std::map<std::string,std::shared_ptr<Task> > tasks;\n'
                      '};\n'
                      '}\n')


def refresh_skill_header():
    path_header = os.getcwd() + '/../../skill/include/skill/'
    path_config = os.getcwd() + '/../../config/'

    file_header = open(path_header + 'header_skills.hpp', 'w')

    with open(path_config + 'active_skills') as f:
        skills = f.read().splitlines()

    file_header.write('#pragma once\n'
                      '\n')

    for s in skills:
        file_header.write('#include "skills/' + s + '.hpp"\n')


def refresh_led_header():
    path_header = os.getcwd() + '/../../led_pattern/include/led_pattern/'
    path_config = os.getcwd() + '/../../config/'

    file_header = open(path_header + 'header_led_patterns.hpp', 'w')

    with open(path_config + 'active_patterns') as f:
        skills = f.read().splitlines()

    file_header.write('#pragma once\n'
                      '\n')

    for s in skills:
        file_header.write('#include "patterns/' + s + '.hpp"\n')
