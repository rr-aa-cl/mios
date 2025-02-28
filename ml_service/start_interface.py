#!/usr/bin/env python3
from interface.interface import Interface
import logging
import sys
import argparse
from threading import Thread


logger = logging.getLogger("ml_service")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Opens and interface (XMLRPC) for Machine Learning Service")
    parser.add_argument("-i","--interface_port", help="changes the default interface port (8000) to INTERFACE_PORT, \
        global Database port is INTERFACE_PORT+1,\n for global Database keep default port!", type=int, default=8000)
    parser.add_argument("-m","--mios_port", help="changes the default mios port (12000) to MIOS_PORT, eg. 13000 for dualarm right", type=int, default=12000)
    parser.add_argument("-d","--mongodb",help="port for Mongo-Database on localhost, default 27017", type=int, default=27017)
    args = parser.parse_args()
    i = Interface(interface_port=args.interface_port, mios_port=args.mios_port, mongo_port=args.mongodb)
    try:
        i.start_rpc_server()
    except KeyboardInterrupt:
        t = Thread(target=i.stop_rpc_server)
        t.start()
        # i.stop_rpc_server()
        print("\nKeyboard interrupt received, exiting.")
        sys.exit(0)
