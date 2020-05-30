#!/usr/bin/python3 -u
import time

#from python.utils.ws_client import *
from udp_client import *


class TestException(Exception):
    pass


def msg_error(assertion, test, msg, rtn):
    if assertion is False:
        print('Error during test: ' + test)
        print(rtn)
        raise TestException(msg)


def system_diagnose(address):
    try:
        test_exception_handling(address)
        test_start_stop(address)
        test_start_wait(address)
        test_multilayer_tasks(address)
        test_subtask_start_stop(address)
        test_task_queue(address)
        skill_tests(address)
        live_parameter_server_test(address)
        test_knowledgebase(address)
        print("System diagnose has revealed no errors.")
    except TestException as e:
        print(e)
        print("System diagnose has failed.")


def test_exception_handling(hostname):
    address = hostname
    print('Testing exception handling...')

    rtn = start_task(address, 'TestTask1', {"parameters": {"exception": "task", "success": True}})
    msg_error(rtn is not None, 'exception_handling_task', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'exception_handling_task', 'Result is false', rtn)
    msg_error('task_uuid' in rtn['result'], 'exception_handling_task', 'Result has no unique task id', rtn)

    rtn = wait_for_task(address,rtn['result']['task_uuid'])
    msg_error(rtn["result"]["task_result"]["results"]["result_code"] == 9,"exception_handling_task",
              "Wrong result code", rtn)

    rtn = start_task(address, 'TestTask1', {"parameters": {'exception': "skill", "success": True}})
    msg_error(rtn is not None, 'exception_handling_skill', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'exception_handling_skill', 'Result is false', rtn)
    msg_error('task_uuid' in rtn['result'], 'exception_handling_skill', 'Result has no unique task id', rtn)

    rtn = wait_for_task(address,rtn['result']['task_uuid'])
    msg_error(rtn["result"]["task_result"]["results"]["t1_s1"]["result_code"] == 5, "exception_handling_task",
              "Wrong result code", rtn)

    rtn = start_task(address, 'TestTask1', {"parameters": {'exception': "control", "success": True}})
    msg_error(rtn is not None, 'exception_handling_control', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'exception_handling_control', 'Result is false', rtn)
    msg_error('task_uuid' in rtn['result'], 'exception_handling_control', 'Result has no unique task id', rtn)

    rtn = wait_for_task(address,rtn['result']['task_uuid'])
    msg_error(rtn["result"]["task_result"]["results"]["t1_s1"]["result_code"] == 1, "exception_handling_task",
              "Wrong result code", rtn)

    rtn = start_task(address, 'TestTask1', {"parameters": {'exception': "invalid", "success": True}})
    msg_error(rtn is not None, 'exception_handling_invalid', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'exception_handling_invalid', 'Result is false', rtn)
    msg_error('task_uuid' in rtn['result'], 'exception_handling_invalid', 'Result has no unique task id', rtn)

    rtn = wait_for_task(address,rtn['result']['task_uuid'])
    msg_error(rtn["result"]["task_result"]["results"]["t1_s1"]["result_code"] == 2, "exception_handling_task",
              "Wrong result code", rtn)

    rtn = start_task(address, 'TestTask1', {"parameters": {'exception': "network", "success": True}})
    msg_error(rtn is not None, 'exception_handling_network', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'exception_handling_network', 'Result is false', rtn)
    msg_error('task_uuid' in rtn['result'], 'exception_handling_network', 'Result has no unique task id', rtn)

    rtn = wait_for_task(address,rtn['result']['task_uuid'])
    msg_error(rtn["result"]["task_result"]["results"]["t1_s1"]["result_code"] == 3, "exception_handling_task",
              "Wrong result code", rtn)

    rtn = start_task(address, 'TestTask1', {"parameters":{"exception": "realtime", "success": True}})
    msg_error(rtn is not None, 'exception_handling_realtime', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'exception_handling_realtime', 'Result is false', rtn)
    msg_error('task_uuid' in rtn['result'], 'exception_handling_realtime', 'Result has no unique task id', rtn)

    rtn = wait_for_task(address,rtn['result']['task_uuid'])
    msg_error(rtn["result"]["task_result"]["results"]["t1_s1"]["result_code"] == 4, "exception_handling_task",
              "Wrong result code", rtn)


def test_start_stop(hostname):
    address = hostname
    url = "http://" + hostname + ":8383"

    # start and various stops after 1 second
    print('Testing exceptional stop...')
    rtn = start_task(address, "TestTask1", queue=True)
    msg_error(rtn['result']['result'], 'start_stop_exception', 'Result is false', rtn)
    task_uuid = rtn["result"]["task_uuid"]
    time.sleep(1)
    rtn = stop_task(address, True)
    msg_error(rtn is not None, 'start_stop_exception', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'start_stop_exception', 'Result is false', rtn)
    rtn = wait_for_task(address, task_uuid)

    msg_error(rtn['result']['task_result']["exception"] is True, 'start_stop_exception', 'Result has no exception', rtn)
    msg_error(rtn['result']['task_result']["success"] is False, 'start_stop_exception', 'Result is successful',
              rtn)
    msg_error(rtn["result"]["task_result"]["results"]["recovered"] is False, "start_stop_exception",
              "Has recovered", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_exception",
              "Wrong error costs", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_exception",
              "Wrong success costs", rtn)


    print('Testing exceptional stop with recovery...')
    rtn = start_task(address, "TestTask1", queue=True)
    msg_error(rtn['result']['result'], 'start_stop_exception', 'Result is false', rtn)
    task_uuid = rtn["result"]["task_uuid"]
    time.sleep(1)
    rtn = stop_task(address, True, recover=True)
    msg_error(rtn is not None, 'start_stop_exception', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'start_stop_exception', 'Result is false', rtn)
    rtn = wait_for_task(address, task_uuid)

    msg_error(rtn['result']['task_result']["exception"] is True, 'start_stop_exception', 'Result has no exception', rtn)
    msg_error(rtn['result']['task_result']["success"] is False, 'start_stop_exception', 'Result is successful',
              rtn)
    msg_error(rtn["result"]["task_result"]["results"]["recovered"] is False, "start_stop_exception",
              "Has recovered", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_exception",
              "Wrong error costs", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_exception",
              "Wrong success costs", rtn)


    print('Testing unsuccessful stop without recovery...')
    rtn = start_task(address, "TestTask1", queue=True)
    msg_error(rtn['result']['result'], 'start_stop_unsuccessful', 'Result is false', rtn)
    task_uuid = rtn["result"]["task_uuid"]
    time.sleep(1)
    rtn = stop_task(address)
    msg_error(rtn is not None, 'start_stop_unsuccessful', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'start_stop_unsuccessful', 'Result is false', rtn)
    rtn = wait_for_task(address, task_uuid)

    msg_error(rtn['result']['task_result']["exception"] is False, 'start_stop_unsuccessful', 'Result has exception', rtn)
    msg_error(rtn['result']['task_result']["success"] is False, 'start_stop_unsuccessful', 'Result is successful',
              rtn)
    msg_error(rtn["result"]["task_result"]["results"]["recovered"] is False, "start_stop_unsuccessful",
              "Recovered", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_unsuccessful",
              "Wrong error costs", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_unsuccessful",
              "Wrong success costs", rtn)

    print('Testing nominal unsuccessful stop with recovery...')
    rtn = start_task(address, "TestTask1", queue=True)
    msg_error(rtn['result']['result'], 'start_stop_unsuccessful_recovery', 'Result is false', rtn)
    task_uuid = rtn["result"]["task_uuid"]
    time.sleep(1)
    rtn = stop_task(address, recover=True)
    msg_error(rtn is not None, 'start_stop_unsuccessful_recovery', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'start_stop_unsuccessful_recovery', 'Result is false', rtn)
    rtn = wait_for_task(address, task_uuid)
    msg_error(rtn['result']['task_result']["exception"] is False, 'start_stop_unsuccessful_recovery', 'Result has exception',
              rtn)
    msg_error(rtn['result']['task_result']["success"] is False, 'start_stop_unsuccessful_recovery', 'Result is successful',
              rtn)
    msg_error(rtn["result"]["task_result"]["results"]["recovered"] is True, "start_stop_unsuccessful_recovery",
              "Not recovered", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_unsuccessful_recovery",
              "Wrong error costs", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_unsuccessful_recovery",
              "Wrong success costs", rtn)

    print('Testing nominal successful stop without recovery...')
    rtn = start_task(address, "TestTask1", queue=True)
    task_uuid = rtn["result"]["task_uuid"]
    time.sleep(1)
    rtn = stop_task(address, success=True)
    msg_error(rtn is not None, 'start_stop_success', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'start_stop_success', 'Result is false', rtn)
    rtn = wait_for_task(address, task_uuid)
    msg_error(rtn['result']['task_result']["exception"] is False, 'start_stop_success',
              'Result has exception',
              rtn)
    msg_error(rtn['result']['task_result']["success"] is True, 'start_stop_success',
              'Result is not successful',
              rtn)
    msg_error(rtn["result"]["task_result"]["results"]["recovered"] is False, "start_stop_success",
              "Recovered", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_success",
              "Wrong error costs", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_success",
              "Wrong success costs", rtn)

    print('Testing nominal successful stop with recovery...')
    rtn = start_task(address, "TestTask1", queue=True)
    msg_error(rtn['result']['result'], 'start_stop_non_nominal', 'Result is false', rtn)
    task_uuid = rtn["result"]["task_uuid"]
    time.sleep(1)
    rtn = stop_task(address, success=True, recover=True)
    msg_error(rtn is not None, 'start_stop_all_true', 'None returned', rtn)
    msg_error(rtn['result']['result'], 'start_stop_success_recovery', 'Result is false', rtn)
    rtn = wait_for_task(address, task_uuid)
    msg_error(rtn['result']['task_result']["exception"] is False, 'start_stop_success_recovery', 'Result has exception',
              rtn)
    msg_error(rtn['result']['task_result']["success"] is True, 'start_stop_success_recovery', 'Result is not successful',
              rtn)
    msg_error(rtn["result"]["task_result"]["results"]["recovered"] is True, "start_stop_success_recovery",
              "Not recovered", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_success_recovery",
              "Wrong error costs", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_success_recovery",
              "Wrong success costs", rtn)
    return


def test_start_wait(hostname):
    address = hostname
    url = "http://" + hostname + ":8383"

    print('Testing execution with successful stop...')
    rtn = start_task(address, "TestTask1", {"parameters":{"success": True}}, queue=True)
    msg_error(rtn['result']['result'], 'start_wait_success', 'Result is false', rtn)
    rtn = wait_for_task(address, rtn['result']['task_uuid'])
    msg_error(rtn['result']['task_result']["exception"] is False, 'start_stop_success_recovery', 'Result has exception',
              rtn)
    msg_error(rtn['result']['task_result']["success"] is True, 'start_stop_success_recovery',
              'Result is not successful',
              rtn)
    msg_error(rtn["result"]["task_result"]["results"]["recovered"] is False, "start_stop_success_recovery",
              "Not recovered", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_success_recovery",
              "Wrong error costs", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_success_recovery",
              "Wrong success costs", rtn)

    print('Testing execution with unsuccessful stop...')
    rtn = start_task(address, "TestTask1", {"parameters":{"success": False}}, queue=True)
    msg_error(rtn['result']['result'], 'start_wait_success', 'Result is false', rtn)
    rtn = wait_for_task(address, rtn['result']['task_uuid'])
    msg_error(rtn['result']['task_result']["exception"] is False, 'start_stop_success_recovery', 'Result has exception',
              rtn)
    msg_error(rtn['result']['task_result']["success"] is False, 'start_stop_success_recovery',
              'Result is not successful',
              rtn)
    msg_error(rtn["result"]["task_result"]["results"]["recovered"] is False, "start_stop_success_recovery",
              "Not recovered", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_success_recovery",
              "Wrong error costs", rtn)
    msg_error(rtn["result"]["task_result"]["cost_suc"] == 0, "start_stop_success_recovery",
              "Wrong success costs", rtn)


def test_multilayer_tasks(address):
    print('Testing two-layer task...')
    rtn = start_task(address, "TestTask2", queue=False, parameters={"parameters":{'d': [1, 2],'e': True,'success': False,
                                                                   'stop_level': 4},
                                                                  "skills": { "t2_s1": {
                                               "skill": {
                                                   "exception": "abc"
                                               }
                                           }
                                       },
                                       'subtasks': {'t2_t1': {'parameters': {
                                           'a': [10, 11,
                                                 12],
                                           'b': True,
                                           'success': True,
                                           "skill_test": 2},
                                           "skills": {
                                               "t1_s2": {
                                                   "skill": {
                                                       "exception": "cba"
                                                   }
                                               }
                                           }}}})
    rtn = wait_for_task(address, rtn['result']['task_uuid'])
    print(rtn)
    results = rtn["result"]["task_result"]["results"]
    msg_error(results["d"] == [1, 2], 'two_layer_task', 'Parameter throughput is faulty.', rtn)
    msg_error(results["e"] == True, 'two_layer_task', 'Parameter throughput is faulty.', rtn)
    msg_error(results["t2_s1"]["exception"] == "abc", 'two_layer_task', 'Parameter throughput is faulty.', rtn)
    msg_error(results["t2_t1"]["t1_s2"]["exception"] == "cba", 'two_layer_task', 'Parameter throughput is faulty.', rtn)
    return

    print('Testing three-layer task...')
    rtn = start_task(address, "TestTask3", queue=False, parameters={'parameters': {'g': [20, 21, 22, 23], 'h': False, 'i': 98.33,
                                                                          'j': 'this is j', 'stop_level': 3,
                                                                          'success': True, },
                    'subtasks': {'t2': {'parameters': {'d': [1, 2],
                                                       'e': True,
                                                       'success': False,
                                                       'stop_level': 4},
                                        'subtasks': {'t1': {'parameters': {
                                            'a': [10, 11,
                                                  12],
                                            'b': True,
                                            'success': True}}}}}})
    wait_for_task(address, rtn['result']['task_uuid'])


def test_subtask_start_stop(address):
    print('Testing non-nominal stop...')
    #input('Press Enter to continue...')
    rtn = start_task(address, "TestTask3", queue=True)
    time.sleep(1)
    stop_task(address)
    wait_for_task(address, rtn["result"]["task_uuid"])

    print('Testing nominal unsuccessful stop without recovery...')
    #input('Press Enter to continue...')
    rtn = start_task(address, "TestTask3", queue=True)
    time.sleep(1)
    stop_task(address, nominal=True)
    wait_for_task(address, rtn["result"]["task_uuid"])

    print('Testing nominal unsuccessful stop with recovery...')
    #input('Press Enter to continue...')
    rtn = start_task(address, "TestTask3", queue=True)
    time.sleep(1)
    stop_task(address, nominal=True, recover=True)
    wait_for_task(address, rtn["result"]["task_uuid"])

    print('Testing nominal successful stop without recovery...')
    #input('Press Enter to continue...')
    rtn = start_task(address, "TestTask3", queue=True)
    time.sleep(1)
    stop_task(address, nominal=True, success=True)
    wait_for_task(address, rtn["result"]["task_uuid"])

    print('Testing nominal successful stop with recovery...')
    #input('Press Enter to continue...')
    rtn = start_task(address, "TestTask3", queue=True)
    time.sleep(1)
    stop_task(address, nominal=True, success=True, recover=True)
    wait_for_task(address, rtn["result"]["task_uuid"])


def test_knowledgebase(address):
    url = "http://" + address + ":8383"
    print("Testing task description download...")
    for i in range(100):
        response = call_method(address, 8383, method="download_task_description", payload={"task": "test_task_1"})
        msg_error(response is not None, "knowledgebase", "Response is none", response)
        msg_error(response["result"]["result"] is True, "knowledgebase", "Could not load task.", response)
        msg_error(response["result"]["description"]["parameters"]["a"] == [1, 2, 3], "knowledgebase", "Task description is faulty.", response)

    print("Testing skill description download...")
    for i in range(100):
        response = call_method(address, 8383, method="download_skill_description", payload={"skill": "test_skill_1"})
        msg_error(response is not None, "knowledgebase", "Response is none", response)
        msg_error(response["result"]["result"] is True, "knowledgebase", "Could not load skill.", response)
        msg_error(response["result"]["description"]["success"] is False, "knowledgebase", "Skill description is faulty.", response)

    print("Testing object description download...")
    for i in range(100):
        response = call_method(address, 8383, method="download_object_description", payload={"object": "test_object_1"})
        msg_error(response is not None, "knowledgebase", "Response is none", response)
        msg_error(response["result"]["result"] is True, "knowledgebase", "Could not load task.", response)
        msg_error(response["result"]["description"]["EE_ob_com"] == [0, 0, 0], "knowledgebase", "Object description is faulty.", response)


def test_task_queue(address):
    url = "http://" + address + ":8383"
    print('Testing queued non-nominal stop...')
    # input('Press Enter to continue...')
    results = []
    for i in range(10):
        results.append(start_task(address, "TestTask1", queue=True))

    call_method(address, 8383, 'remove_task', {'task_uuid': results[0]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[6]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[9]['result']['task_uuid']})
    time.sleep(1)
    stop_task(address)
    time.sleep(0.5)
    wait_for_task(address, results[8]['result']['task_uuid'])
    wait_for_task(address, results[9]['result']['task_uuid'])

    print('Testing queued nominal unsuccessful stop without recovery...')
    # input('Press Enter to continue...')
    results = []
    for i in range(10):
        results.append(start_task(address, "TestTask1", queue=True))

    call_method(address, 8383, 'remove_task', {'task_uuid': results[0]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[6]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[9]['result']['task_uuid']})
    stop_task(address, nominal=True)
    wait_for_task(address, results[5]['result']['task_uuid'])
    wait_for_task(address, results[8]['result']['task_uuid'])
    wait_for_task(address, results[9]['result']['task_uuid'])

    print('Testing queued nominal unsuccessful stop with recovery...')
    # input('Press Enter to continue...')
    results = []
    for i in range(10):
        results.append(start_task(address, "TestTask1", queue=True))

    call_method(address, 8383, 'remove_task', {'task_uuid': results[0]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[6]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[9]['result']['task_uuid']})
    stop_task(address, nominal=True, recover=True)
    wait_for_task(address, results[5]['result']['task_uuid'])
    wait_for_task(address, results[8]['result']['task_uuid'])
    wait_for_task(address, results[9]['result']['task_uuid'])

    print('Testing queued nominal successful stop without recovery...')
    # input('Press Enter to continue...')
    results = []
    for i in range(10):
        results.append(start_task(address, "TestTask1", queue=True))

    call_method(address, 8383, 'remove_task', {'task_uuid': results[0]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[6]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[9]['result']['task_uuid']})
    stop_task(address, nominal=True, success=True)
    wait_for_task(address, results[5]['result']['task_uuid'])
    wait_for_task(address, results[8]['result']['task_uuid'])
    wait_for_task(address, results[9]['result']['task_uuid'])

    print('Testing queued nominal successful stop with recovery...')
    # input('Press Enter to continue...')
    results = []
    for i in range(10):
        results.append(start_task(address, "TestTask1", queue=True))

    call_method(address, 8383, 'remove_task', {'task_uuid': results[0]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[6]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[9]['result']['task_uuid']})
    stop_task(address, nominal=True, success=True, recover=True)
    wait_for_task(address, results[5]['result']['task_uuid'])
    wait_for_task(address, results[8]['result']['task_uuid'])
    wait_for_task(address, results[9]['result']['task_uuid'])

    print('Testing queued nominal successful stop with recovery and empty queue...')
    # input('Press Enter to continue...')
    results = []
    for i in range(10):
        results.append(start_task(address, "TestTask1", queue=True))

    call_method(address, 8383, 'remove_task', {'task_uuid': results[0]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[6]['result']['task_uuid']})
    call_method(address, 8383, 'remove_task', {'task_uuid': results[9]['result']['task_uuid']})
    stop_task(address, nominal=True, success=True, recover=True, empty_queue=True)
    wait_for_task(address, results[5]['result']['task_uuid'])
    wait_for_task(address, results[8]['result']['task_uuid'])
    wait_for_task(address, results[9]['result']['task_uuid'])


def skill_tests(address):
    url = "http://" + address + ":8383"

    # print('Testing repetitive skill execution...')
    # rtn = rpc_call(url, 'start_task', {'task': 'test_task_1', 'queue': True, 'parameters': {'skill_test': 1}})
    # rpc_call(url, 'wait_for_task', {'task_uuid': rtn['result']['task_uuid']})
    #
    # print('Testing repetitive skill execution with object...')
    # rtn = rpc_call(url, 'start_task', {'task': 'test_task_1', 'queue': True, 'parameters': {'skill_test': 3}})
    # rpc_call(url, 'wait_for_task', {'task_uuid': rtn['result']['task_uuid']})

    print('Testing parallel thread...')
    response = start_task(address, "TestTask1", queue=True, parameters={'parameters': {'skill_test': 2}})
    response = wait_for_task(address, response['result']['task_uuid'])
    msg_error(response is not None, 'live_parameter_server', 'None returned', response)
    eval = response["result"]["eval"]
    msg_error("parallels_cnt" in eval["results"]["t1_s2"], 'parallels_thread', 'Parallels counter not in results', response)
    msg_error(eval["results"]["t1_s2"]["parallels_cnt"] > 290, 'parallels_thread',
              'Parallels counter is wrong.', response)

    return
    print('Testing skill pause...')
    rtn = rpc_call(url, 'start_task', {'task': 'test_task_1', 'queue': True, 'parameters': {'skill_test': 2}})
    time.sleep(1)
    rpc_call(url,'toggle_skill_pause',{'pause':True})
    time.sleep(2)
    rpc_call(url, 'toggle_skill_pause', {'pause': False})
    rpc_call(url, 'wait_for_task', {'task_uuid': rtn['result']['task_uuid']})

    # pause skill execution
    # trigger skill conditions
    # exception handling check
    pass


def live_parameter_server_test(address):
    url_parameter_server = "http://" + address + ":8384"

    print("Testing live parameter server...")
    response = start_task(address, "TestTask1", queue=True, parameters={'parameters': {'skill_test': 2}})
    time.sleep(1)
    response_set1 = call_method(address, 8383, "set_parameter", {"parameter_key": "test_parameter_1", "parameter_value": 42}, 8384)
    msg_error(response is not None, 'live_parameter_server', 'None returned', response_set1)
    response_set2 = call_method(address, 8383, "set_parameter", {"parameter_key": "test_parameter_2", "parameter_value": "hello world"})
    msg_error(response is not None, 'live_parameter_server', 'None returned', response_set2)
    response_set3 = call_method(address, 8383, "set_parameter", {"parameter_key": "test_parameter_3", "parameter_value": [1,2,3,4,5]})
    msg_error(response is not None, 'live_parameter_server', 'None returned', response_set3)
    response = wait_for_task(address, response['result']['task_uuid'])
    msg_error(response is not None, 'live_parameter_server', 'None returned', response)
    msg_error(response is not None, 'live_parameter_server', 'None returned', response)
    msg_error("result" in response, 'live_parameter_server', 'None returned', response)
    eval = response["result"]["eval"]
    msg_error("test_parameter_1" in eval["results"]["t1_s2"], 'live_parameter_server', 'Test parameter not in results', response)
    msg_error("test_parameter_2" in eval["results"]["t1_s2"], 'live_parameter_server', 'Test parameter not in results', response)
    msg_error("test_parameter_3" in eval["results"]["t1_s2"], 'live_parameter_server', 'Test parameter not in results', response)
    msg_error(eval["results"]["t1_s2"]["test_parameter_1"]==42, 'live_parameter_server', 'test_parameter_1 has not been put through.', response)
    msg_error(eval["results"]["t1_s2"]["test_parameter_2"] == "hello world", 'live_parameter_server',
              'test_parameter_2 has not been put through.', response)
    msg_error(eval["results"]["t1_s2"]["test_parameter_3"] == [1,2,3,4,5], 'live_parameter_server',
              'test_parameter_3 has not been put through.', response)


def gripper_tests(url):
    # grasp test object, frame check
    # release object, frame check
    # home gripper
    pass


def desk_tests(url):
    # execute timeline and stop
    pass


def general_function_tests(url):
    # lock/unlock brakes
    # pack pose
    # shutdown
    pass


def info_function_tests(url):
    # state check
    # ip check
    pass
