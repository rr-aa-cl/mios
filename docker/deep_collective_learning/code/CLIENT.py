import xmlrpc.client
import time


with xmlrpc.client.ServerProxy("http://0.0.0.0:9000") as s:
    s.start_recording()
    time.sleep(5)
    s.end_recording()
    
