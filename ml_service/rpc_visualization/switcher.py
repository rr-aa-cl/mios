import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer
import socket
from DataBuffer import DataBuffer
import sys
import threading
import ifaddr
import math

# 8002 switch rpc server
# 8003 switch udp server
# 8004 tensorboard client

class tensorboard_client:
    """tensorboard xmlrpc client class"""
    def __init__(self, host, port) -> None:
        """__init__

        Args:
            host (_type_): tensorboard xmlrpc server ip
            port (_type_): tensorboard xmlrpc server port
        """
        print("server info: ", (host, str(port)))
        self.proxy = xmlrpc.client.ServerProxy("http://%s:%s/" %(host, str(port))) 
        self.count = 0
        self.hostname = socket.gethostname()
        print("server info: ", (host, str(port)))
    
    # deconstructor
    def __del__(self):
        print("deconstructor")
        
    def send(self, n):
        # for the collective learning the        
        try:    
            self.proxy.plot(self.hostname, n, self.count)
            print("vis send:", (n, self.count))
            self.count += 1
            flag = 0
        except:
            print("failed to send the message",  (self.hostname, n, self.count))

def get_ip() -> str:
    # Get a list of all network interfaces, add return the one begin with "10."
    adapters = ifaddr.get_adapters()

    # Loop through the list of adapters
    for adapter in adapters:
        # Check if the adapter is connected to a network
        if adapter.ips:
            # Loop through the list of IP addresses for this adapter
            for ip in adapter.ips:
                # Print the IP address
                if isinstance(ip.ip, str):	
                    x = ip.ip.split(".")[0]
                    print((x, ip.ip))
                    if x == "10":
                        return ip.ip
    
    return "0.0.0.0"

class switcher(): 
    def __init__(self): 
        self.vis_buffer = DataBuffer()
        self.server = SimpleXMLRPCServer(((get_ip(), 8002)), allow_none=True) 
        self.server_socket = None
        self.proxy = None
        self.flag = 0
    
    def start_server(self): 
        print ("Server thread started. Testing the server...") 
        self.server.register_function(self.send_start, "send_start")
        self.server.register_function(self.send_off, "send_off")
        self.server.register_function(self.empty_buffer, "empty_buffer")
        self.server.serve_forever() 
        
    def stop_server(self):
        self.server.server_close()
        self.server.shutdown()
        print("Tensorboard server stop")

    def UDP_start(self):
        # socket UDP server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(("localhost", 8003))
        print("UDP server started")
        while True:
            data, _ = self.server_socket.recvfrom(1024)
            print("received message: ", data.decode("utf-8"))
            value = float(data.decode("utf-8"))
            if math.isinf(value):
                pass
            else:
                self.vis_buffer.add_data(value)
    
    def send_start(self, ip="10.157.175.142", port="8004"):
        self.proxy = tensorboard_client(ip, port)        
        self.flag = 1
            
    def send_off(self):
        self.flag = 0
        print("send off")
    
    def send_data(self):    
        while True:
            if self.flag:
                n = self.vis_buffer.get_data()
                self.proxy.send(n)
                print("send message: ", (n, self.proxy.count))
            else:
                pass       
    
    def empty_buffer(self):
        self.vis_buffer.empty_buffer()    

   

if __name__ == "__main__":
    try:
        witch = switcher()
        t1 = threading.Thread(target=witch.UDP_start)
        t1.start()
        t2 = threading.Thread(target=witch.send_data)
        t2.start()
        witch.start_server()
    except KeyboardInterrupt:
        witch.stop_server()
        witch.server_socket.close()
        print("UDP server stop")
        sys.exit(0)