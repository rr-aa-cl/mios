#!/usr/bin/env python3
from interface.interface import Interface
import logging
import sys
import os
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
        global Database port is INTERFACE_PORT+1,\n for global Database keep default port!", type=int, default=False)
    parser.add_argument("-m","--mios_port", help="changes the default mios port (12000) to MIOS_PORT, eg. 13000 for dualarm right", type=int, default=False)
    parser.add_argument("-d","--mongodb",help="port for Mongo-Database on localhost, default 27017", type=int, default=False)
    args = parser.parse_args()
    if not args.interface_port:
        logger.debug("No interface port specified, searching env...")
        interface_port = os.getenv("interface_port")
        if interface_port is None:
            logger.debug("No interface_port found in env. Fall back to default: 8000")
            interface_port = 8000
    else:
        interface_port = args.interface_port

    if not args.mios_port:
        logger.debug("No mios port specified, searching env...")
        mios_port = os.getenv("mios_port")
        if mios_port is None:
            logger.debug("No mios_port found in env. Fall back to default: 12000")
            mios_port = 12000
    else:
        mios_port = args.interface_port

    if not args.mongodb:
        logger.debug("No mongodb port specified, searching env...")
        mongodb = os.getenv("mongodb")
        if mongodb is None:
            logger.debug("No interface_port found in env. Fall back to default: 27017")
            mongodb = 27017
    else:
        mongodb = args.interface_port

    

    logger.debug("Start ml_service with on port "+str(interface_port)+" for mios instance at port "+str(mios_port))
    i = Interface(interface_port=int(interface_port), mios_port=int(mios_port), mongo_port=int(mongodb))
    try:
        i.start_rpc_server()
    except KeyboardInterrupt:
        t = Thread(target=i.stop_rpc_server)
        t.start()
        # i.stop_rpc_server()
        print("\nKeyboard interrupt received, exiting.")
        sys.exit(0)
