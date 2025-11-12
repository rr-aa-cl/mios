import asyncio
import threading
import socket
from  utils.ws_client import *

'''
This bootstraps the ws.client call_method to use a global event loop.
This is not just more efficient than creating a new event_loop for every call_method, but it also allows for threadsafe communication.
'''

# --- 1. Setup the global event loop ---
MAIN_EVENT_LOOP = asyncio.get_event_loop()
_loop_thread = threading.Thread(target=MAIN_EVENT_LOOP.run_forever, daemon=True)
_loop_thread.start()

# --- 2. Define the NEW, EFFICIENT implementation of call_method ---
def threadsafe_call_method(hostname: str, port: int, method, payload=None, endpoint="mios/core", timeout=100, silent=False):
    """
    A synchronous, thread-safe, and efficient implementation that uses the shared event loop.
    """
    try:
        request = {
            "method": method,
            "request": payload
        }
        # The core async logic we want to run
        coro = send(hostname, request=request, port=port,
                               endpoint=endpoint, timeout=timeout, silent=silent)
        
        # Submit the coroutine to the long-running loop and wait for the result
        future = asyncio.run_coroutine_threadsafe(coro, MAIN_EVENT_LOOP)
        return future.result(timeout=timeout + 5) # Use a slightly longer timeout here

    except socket.gaierror as e:
        print(e)
        print(f"Hostname: {hostname}, port:{port}, endpoint: {endpoint}, method: {method}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in call_method: {e}")
        print(f"Hostname: {hostname}, port:{port}, endpoint: {endpoint}, method: {method}")
        return None
    

# --- 3. Apply the patch ---
call_method = threadsafe_call_method
print("`\\_applied threadsafe patch to call_method_/´")