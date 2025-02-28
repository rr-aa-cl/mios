import threading

class DataBuffer:
    def __init__(self):
        self.buffer = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        print("DataBuffer for visulization is initialized!")

    def add_data(self, data):
        with self.lock:
            self.buffer.append(data)
            # notify waiting threads that new data is available
            self.condition.notify_all()

    def get_data(self):
        with self.lock:
            # wait until there is data in the buffer
            while len(self.buffer) == 0:
                self.condition.wait()
            # get the data from the buffer
            return self.buffer.pop(0)
        
    def empty_buffer(self):
        with self.lock:
            self.buffer = [] 
                
    
     
# In the above example, we've added a new condition attribute to the DataBuffer class, which is initialized with a Condition 
# object that is associated with the lock. The add_data() method now notifies all waiting threads that new data is available 
# by calling self.condition.notify_all() after adding data to the buffer.

# The get_data() method now waits until there is data in the buffer by calling self.condition.wait() inside a loop. This 
# releases the lock and blocks the calling thread until another thread calls notify() or notify_all() on the same condition 
# variable. Once new data is available, the loop exits and the method retrieves and returns the data from the buffer.

# To detect when new data is available, you can use a separate thread that continuously calls the get_data() method and 
# processes the returned data. Here's an example of how you might use this in a separate thread:

def process_data(buffer):
    while True:
        data = buffer.get_data()
        # process the data...

# In this example, the process_data() function is called in a separate thread and continuously calls get_data() to retrieve 
# new data from the buffer. When new data is available, it processes the data in some way (which you would replace with your own code).