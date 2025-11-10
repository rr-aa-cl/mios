import logging
import threading

logger = logging.getLogger("ml_service")

class DataBuffer:
    def __init__(self):
        self.buffer = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def add_data(self, data):
        with self.lock:
            self.buffer.append(data)
            # notify waiting threads that new data is available
            self.condition.notify_all()
            logger.debug("DataBuffer::add_data, current size: "+str(len(self.buffer)))
    
    def readd_data(self,data):
        with self.lock:
            self.buffer.insert(0,data)
            # notify waiting threads that new data is available
            self.condition.notify_all()
            # logger.debug("DataBuffer::readd_data, current size: "+str(len(self.buffer)))

    def get_data(self, timeout=None):
        with self.lock:
            result = None
            # wait until there is data in the buffer
            while len(self.buffer) == 0:
                self.condition.wait(timeout=timeout)
            # get the data from the buffer
            try:
                result = self.buffer.pop(0)
            except IndexError:
                pass
            return result
        
    def empty_buffer(self):
        with self.lock:
            self.buffer = [] 
            
    def get_size(self):
        return len(self.buffer)
                
    
