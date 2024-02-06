from run_experiments import *

# ---------------------------- exp robots ------------------------------------
list_robots = list_block_1 + list_block_2 + list_U
print(len(list_robots))

# ---------------------------- cutoff cost ------------------------------------
cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
            '003_left': 0.68016,
            '004_left': 0.74976,
            '005_left': 0.65, #
            '006_left': 0.6127199999999999,
            '007_left': 0.62616,
            '008_left': 0.6371999999999999,
            '010_left': 0.6888000000000001,
            '011_left': 0.63816,
            '012_left': 0.75528,
            '009_left': 0.6943199999999999,
            '013_left': 0.6348,
            '014_left': 0.6,
            '015_left': 0.68184,
            '016_left': 0.9,   #
            '017_left': 0.63864,
            '041_left': 0.63144,
            '021_left': 0.63528,
            '022_left': 0.6828000000000001,
            '023_left': 0.6648000000000001,
            '024_left': 0.9187199999999999,
            '025_left': 0.64752,
            '027_left': 0.68448,
            '028_left': 0.61824,
            '029_left': 0.68088}
# -----------------------------------------------------------------------------


def ten_agent_collective():
    modules = list_robots
    
    # sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()    
   
    tags = ["10agents_25tasks","collective","ps_alpha_5_reverse"]
    modules.reverse()
    # tags = ["test run"]
        
        
    # for n_current_iter in range(29,30): #range(15,25):   (not reserve)
    for n_current_iter in range(10): # reverse one
        tasks = {}
        #tasks = {"collective-014.rsi.ei.tum.de":["014_left"]}  #  do this task at first
        for xxx in modules: 
            tasks["collective-"+str(xxx)+".rsi.ei.tum.de"] = [str(xxx)+"_left"]
        threads = []
        print("Number of iteration: ", n_current_iter+1)
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
        knowledge_source.mode = "global"  # None  # 
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1))
        knowledge_source.type = "all"
            
        dualarm_skills = []
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()

        threads = []
        while len(tasks) > 0:
            robot = list(tasks.keys())[0]
            insertable = tasks.pop(robot)[0]  #first index because every robot has just one object
            container = insertable+"_container"
            approach = container+"_approach"
            pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
            if not get_states([insertable[:3]])[0]:
                print(robot, "is not ready! Skipping task ",insertable)
                continue
            if insertable in cutoff:
                sc.finish_cost = cutoff[insertable]
            if insertable == "010_left" or insertable == "023_left" or insertable == "027_left":
                print("increase limits for ",insertable)
                pd.domain.limits["p2_f_push_z"] = (0,60)
            dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
            threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)))
            threads[-1].start()
            time.sleep(1)
            server = ServerProxy("http://%s:%s/" %(robot, "8000"))
            if server.start_telemetry("10.157.175.246", 8004):
                print("start sending telemetry")
            while sum([t.is_alive() for t in threads]) >= 10:  # 5 agents are running in parallel
                time.sleep(1)

        for t in threads:
            t.join()
        tensor_server = ServerProxy("http://10.157.175.246:8004")
        tensor_server.stop()
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()
        print("run ", n_current_iter, " finished :)")
    return "finished :)"



def var_agent_collective(n_agents: int, n_current_iter:int, tags:list, reverse=False):
    modules = copy.deepcopy(list_robots)
    # sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()    
   
    #tags = ["10agents_25tasks","collective","ps_alpha_5_reverse"]
    if reverse:
        modules.reverse()
    # tags = ["test run"]
        
        
# for n_current_iter in range(29,30): #range(15,25):   (not reserve)
    tasks = {}
    #tasks = {"collective-014.rsi.ei.tum.de":["014_left"]}  #  do this task at first
    for xxx in modules: 
        tasks["collective-"+str(xxx)+".rsi.ei.tum.de"] = [str(xxx)+"_left"]
    threads = []
    print("Number of iteration: ", n_current_iter+1)
    knowledge_source = Knowledge()
    knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
    knowledge_source.mode = "global"  # None  # 
    knowledge_source.scope = []
    knowledge_source.scope.extend(tags)
    knowledge_source.scope.append("n"+str(n_current_iter+1))
    knowledge_source.type = "all"
        
    dualarm_skills = []
    move_context = {
                "skill": {
                    "speed": 0.5,
                    "acc": 1,
                    "q_g": [0, 0, 0, 0, 0, 0, 0],
                    "objects": {
                        "goal_pose": "hold"}},
                "control": {
                    "control_mode": 3},
                "user": {
                    "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                    "F_ext_max": [100, 50]}}
    dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
    
    kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
    kb.clear_memory()

    threads = []
    while len(tasks) > 0:
        robot = list(tasks.keys())[0]
        insertable = tasks.pop(robot)[0]  #first index because every robot has just one object
        container = insertable+"_container"
        approach = container+"_approach"
        pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                {"Insertable": insertable, "Container": container,
                                "Approach": approach}).get_problem_definition(insertable)
        if not get_states([insertable[:3]])[0]:
            print(robot, "is not ready! Skipping task ",insertable)
            continue
        if insertable in cutoff:
            sc.finish_cost = cutoff[insertable]
        if insertable == "010_left" or insertable == "023_left" or insertable == "027_left":
            print("increase limits for ",insertable)
            pd.domain.limits["p2_f_push_z"] = (0,60)
        dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
        threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)))
        threads[-1].start()
        time.sleep(1)
        #server = ServerProxy("http://%s:%s/" %(robot, "8000"))
        #if server.start_telemetry("10.157.175.246", 8004):
        #    print("start sending telemetry")

        while sum([t.is_alive() for t in threads]) >= n_agents:  # n_agents are running in parallel
            time.sleep(1)

    for t in threads:
        t.join()
    #tensor_server = ServerProxy("http://10.157.175.246:8004")
    #tensor_server.stop()
    kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
    kb.clear_memory()
    print("run ", n_current_iter, " finished :)")
    return "finished :)"

def alpha_experiment():
    for i in range(10):  # iteration
        for n in range(6,10):
            var_agent_collective(n,i, [str(n)+"agents_25tasks","collective","ps_alpha_var"])

def alpha_experiment_second():
    for i in range(10):  # iteration
        for n in range(1,5):
            var_agent_collective(n,i, [str(n)+"agents_25tasks","collective","ps_alpha_var"])
