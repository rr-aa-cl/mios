# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 13:40:00 2025

@author: Lingyun

Handles loading of configuration from a JSON file. Creates a template if none exists.
"""
import json
import sys
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR/'config.json'

ROBOT_IP = os.getenv("ROBOT_IP")
if ROBOT_IP is None:
  ROBOT_IP = "127.0.0.1"
ROBOT_USER = os.getenv("ROBOT_USER")
if ROBOT_USER is None:
  ROBOT_USER = "<user-name>"
ROBOT_PASSWORD = os.getenv("ROBOT_PASSWORD")
if ROBOT_PASSWORD is None:
  ROBOT_PASSWORD = "<user-password>"
MONGONAME = os.getenv("MONGONAME")
if MONGONAME is None:
  MONGONAME = "mios"

DEFAULT_CONFIG = {
  "api_settings": {
    "robot_ip": "https://"+ROBOT_IP,
    "username": ROBOT_USER,
    "password": ROBOT_PASSWORD,
    "mongo_name": MONGONAME,
    "enable_proxy": False,
    "socks5_proxy": "socks5h://127.0.0.1:1080"
  },
  "keep_alive_settings": {
    "check_interval_secs": 60,
    "retry_delay_secs": 0,
    "owner_name": "AutomatedResearch",
    "self_test_trigger_mins": 60,
    "action_on_threshold": "self-test"
  }
}

def load_config():
    """
    Loads the configuration from config.json. If the file does not exist,
    it creates a template and exits the program.
    """
    return DEFAULT_CONFIG
    # if not os.path.exists(CONFIG_FILE):
    #     print(f"Configuration file '{CONFIG_FILE}' not found.", flush=True)
    #     try:
    #         with open(CONFIG_FILE, 'w') as f:
    #             json.dump(DEFAULT_CONFIG, f, indent=2)
    #         print(f"A new  '{CONFIG_FILE}' has been created with environmane variable informations.", flush=True)
    #         #print("Please edit it with your robot's IP address and credentials before running the script again.", flush=True)
    #     except IOError as e:
    #         print(f"Error creating configuration file: {e}", flush=True)
    #     #sys.exit(1) # Exit after creating the template

    # try:
    #     with open(CONFIG_FILE, 'r') as f:
    #         return json.load(f)
    # except (json.JSONDecodeError, IOError) as e:
    #     print(f"Error reading configuration file '{CONFIG_FILE}': {e}", flush=True)
    #     print("Please ensure it is a valid JSON file.", flush=True)
    #     sys.exit(1)
