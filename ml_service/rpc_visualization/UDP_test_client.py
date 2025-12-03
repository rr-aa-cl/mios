import socket
import time


if __name__ == "__main__":
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    for a in range(100):
        s.sendto(str(a).encode(), ("localhost", 8003))
        time.sleep(0.5)
    
    
    # s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # s.sendto(str(a).encode(), ("localhost", 8003))
    