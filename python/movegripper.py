from utils.ws_client import start_task, wait_for_task, call_method


if __name__ == "__main__":

    robot="127.0.0.1"
    port = 12000
    res=call_method(robot, port, "get_state")
    print(str(res))
    #move_gripper(robot, 0)
    cur_width=call_method(robot, port, "get_state")["result"]["gripper_width"]
    print("janine: " + str(cur_width))
    #if cur_width > 0.01:
     #   res=call_method(robot, port, "move_gripper", {"speed":1, "force":1, "width":cur_width-0.03})
    #else: 
    res=call_method(robot, port, "move_gripper", {"speed":1, "force":1, "width":0.013})
    print(str(res))
