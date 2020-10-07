#!/usr/bin/env python3
from interface.interface import Interface
import logging
import sys
from threading import Thread


logger = logging.getLogger("ml_service")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


if __name__ == "__main__":
    i = Interface()
    try:
        i.start_rpc_server()
    except KeyboardInterrupt:
        t = Thread(target=i.stop_rpc_server)
        t.start()
        # i.stop_rpc_server()
        print("\nKeyboard interrupt received, exiting.")
        sys.exit(0)
