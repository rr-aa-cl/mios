from run_experiments import *

handguiding_task = None

def handguiding(robot):
    context = {
        "skill": {
            "record_trajectory": False,
            #"recording_length": 1,
            #"recording_name": None,
            
        },
        "control": {
            "control_mode": 0
        }
    }
    handguiding_task = Task(robot)
    handguiding_task.add_skill("record_trajectory", "HandGuiding", context)
    handguiding_task.start()
    input("Press any key, if you finished handguiding.")
    result = handguiding_task.stop()
    #print("Result: " + str(result))

def learn_single_insertion(robot, insertable, tags= ["demorun"]):
    learn_insertion(robot, insertable+"_container_approach", insertable, insertable+"_container", tags)

def best_insertion(robot, insertable, tags= ["demorun"]):
    context = download_best_result_2(robot, "ml_results","insertion", insertable,"")
    print("Press [ctl+c] to stop play your best results" )
    try:
        while True:
            t = Task(robot)
            t.add_skill("best_insertion", "TaxInsertion", context)
            t.start()
            t.wait()
    except KeyboardInterrupt:
        pass

def teach_insertion(robot, insertable, mios_port=12000):
    input("Press key to start teaching. [Pose above container, without object]")
    handguiding(robot)
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container_above"})
    print("\nTeach where to grab object [gripper will close]")
    handguiding(robot)
    #call_method(robot, mios_port, "grasp", {"width":0,"speed":1,"force":100})
    #current_finger_width = call_method(robot,mios_port,"get_state")["result"]["gripper_width"]
    #call_method(robot,mios_port,"move_gripper",{"speed":1,"force":100,"width":current_finger_width+0.005})
    call_method(robot, mios_port, "grasp", {"width":0,"speed":1,"force":100,"epsilon_outer":1})
    call_method(robot, mios_port, "teach_object", {"object": insertable, "teach_width":True})
    call_method(robot, mios_port, "set_grasped_object", {"object": insertable})
    #time.sleep(1)
    #print("closing gripper")
    #print(call_method(robot, mios_port, "grasp_object", {"object": insertable}))
    print("\nTeach approach pose[with object]")
    handguiding(robot)
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container_approach"})
    print("\nTeach container [with object]")
    handguiding(robot)
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container"})

def iros_leanring():
    pass
