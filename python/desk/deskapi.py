# -*- coding: utf-8 -*-
"""
Created on Thu Sep 4 00:56:31 2025

@author: Lingyun
"""

import requests
import os
from requests.auth import HTTPBasicAuth
from typing import Optional, Tuple
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import time
from mongodb_client import MongoDBClient
import config_loader

# --- Suppress InsecureRequestWarning ---
urllib3.disable_warnings(InsecureRequestWarning)

# ---------------- Load Configuration ----------------
config = config_loader.load_config()
api_config = config['api_settings']

ROBOT_IP = api_config['robot_ip']
USERNAME = api_config['username']
PASSWORD = api_config['password']
MONGONAME = api_config['mongo_name']
ENABLE_PROXY = api_config['enable_proxy']
SOCKS5_PROXY = api_config['socks5_proxy']

# ---------------- Global Setup ----------------
proxies = {
    "http": SOCKS5_PROXY,
    "https": SOCKS5_PROXY,
}

auth = HTTPBasicAuth(USERNAME, PASSWORD)

def _make_request(method, url, **kwargs) -> Tuple[bool, dict]:
    """A centralized request function to handle errors and proxy settings."""
    try:
        current_proxies = proxies if kwargs.pop('use_proxy', ENABLE_PROXY) else None
        
        kwargs.setdefault('verify', False)
        kwargs.setdefault('proxies', current_proxies)
        kwargs.setdefault('auth', auth)

        r = requests.request(method, url, **kwargs)
        
        if r.status_code in [200, 201, 202] and r.content:
            return True, r.json()
        elif r.status_code == 204:
            return True, {"status": "Success (No Content)"}
            
        r.raise_for_status()
        
        return True, r.json() if r.content else {"status": "Success"}

    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}
    except ValueError:
        return False, {"error": f"Received non-JSON response with status code {r.status_code}"}


def save_token(token: str):
    """Saves the control token to MongoDB (mios->parameter->system)."""

    mongo_client = MongoDBClient("localhost",27017)
    mongo_client.update(MONGONAME,"parameters",{"name":"system"},{"spoc_token":token})


def load_token() -> Optional[str]:
    """Loads the control token from MongoDB (mios->parameter->system)."""
    try:
        mongo_client = MongoDBClient("localhost",27017)
        mios_system_conf = mongo_client.read(MONGONAME,"parameters",{"name":"system"})[0]
        
    except:
        print(f"Cannot find token in MongoDB {MONGONAME}.", flush=True)
        return None
    try:
        return mios_system_conf["spoc_token"]
    except KeyError as e:
        print(f'load_token error: {e}', flush=True)
    return None

def clear_token():
    """Deletes the local control token file."""
    mongo_client = MongoDBClient("localhost",27017)
    mongo_client.update(MONGONAME,"parameters",{"name":"system"},{"spoc_token":""})

# ---------------- Control Token ----------------

def take_control(owner="franka", timeout=None) -> Tuple[bool, dict]:
    url = f"{ROBOT_IP}/api/system/control-token:take"
    body = {"owner": owner}
    if timeout:
        body["timeout"] = timeout
    
    success, response = _make_request("POST", url, json=body)
    if success and "token" in response:
        save_token(response["token"])
        return True, {"message": f"Token acquired: {response['token']}"}
    return success, response

def release_control() -> Tuple[bool, dict]:
    token = load_token()
    if not token:
        return False, {"error": "No control token to release."}
    url = f"{ROBOT_IP}/api/system/control-token:release"
    headers = {"X-Control-Token": token}
    
    success, response = _make_request("POST", url, headers=headers)
    if success:
        clear_token()
        return True, {"message": "Control token released."}
    return success, response

def get_control_status() -> Tuple[bool, dict]:
    url = f"{ROBOT_IP}/api/system/control-token"
    return _make_request("GET", url)

def enforce_control(owner="franka") -> Tuple[bool, dict]:
    success, data = get_control_status()
    if success:
        owner_status = data.get("owner")
        if owner_status and owner_status != owner:
            print(f"Token currently held by {owner_status}. Forcing new token.", flush=True)
    return take_control(owner=owner)

# ---------------- Robot Arm ----------------

def get_joint_states() -> Tuple[bool, dict]:
    """Gets the status of all joints and summarizes their brake status."""
    url = f"{ROBOT_IP}/api/arm/joints"
    success, response_data = _make_request("GET", url)
    if not success:
        return False, response_data

    if isinstance(response_data, list) and all('brakeStatus' in j for j in response_data):
        statuses = {j['brakeStatus'] for j in response_data}
        summary = "Unknown"
        if len(statuses) == 1:
            summary = statuses.pop()
        elif len(statuses) > 1:
            summary = "Mixed"
        return True, {"status": summary, "details": response_data}
    
    return False, {"error": "Invalid joint states response format"}

def unlock_joints() -> Tuple[bool, dict]:
    token = load_token()
    if not token:
        return False, {"error": "Cannot unlock joints without a control token."}
    url = f"{ROBOT_IP}/api/arm/joints:unlock"
    headers = {"X-Control-Token": token}
    return _make_request("POST", url, headers=headers)

def lock_joints() -> Tuple[bool, dict]:
    url = f"{ROBOT_IP}/api/arm/joints:lock"
    return _make_request("POST", url)

# ---------------- FCI ----------------

def activate_fci() -> Tuple[bool, dict]:
    """Checks operating mode, switches to Execution if necessary, then activates FCI."""
    mode_success, mode_data = get_operating_mode()
    if not mode_success:
        return False, {"error": f"Could not get operating mode: {mode_data.get('error', 'Unknown')}"}

    current_mode = mode_data.get('status')
    
    if current_mode == 'Programming':
        print("Switching to Execution mode before activating FCI.", flush=True)
        switch_success, switch_result = switch_to_execution()
        if not switch_success:
            return False, {"error": f"Failed to switch to Execution: {switch_result.get('error', 'Unknown')}"}
        time.sleep(1)

    token = load_token()
    if not token:
        return False, {"error": "Cannot activate FCI without a control token."}
    url = f"{ROBOT_IP}/api/fci:activate"
    headers = {"X-Control-Token": token}
    return _make_request("POST", url, headers=headers)

def deactivate_fci() -> Tuple[bool, dict]:
    token = load_token()
    if not token:
        return False, {"error": "Cannot deactivate FCI without a control token."}
    url = f"{ROBOT_IP}/api/fci:deactivate"
    headers = {"X-Control-Token": token}
    return _make_request("POST", url, headers=headers)

def get_fci_status() -> Tuple[bool, dict]:
    url = f"{ROBOT_IP}/api/fci"
    return _make_request("GET", url)

# ---------------- End Effector ----------------

def get_end_effector_power_status() -> Tuple[bool, dict]:
    """Gets the power status of the end effector."""
    url = f"{ROBOT_IP}/api/end-effector/power"
    return _make_request("GET", url)

def power_on_end_effector() -> Tuple[bool, dict]:
    """Powers on the end effector."""
    token = load_token()
    if not token:
        return False, {"error": "Cannot power on end effector without a control token."}
    url = f"{ROBOT_IP}/api/end-effector/power:on"
    headers = {"X-Control-Token": token}
    return _make_request("POST", url, headers=headers)

def power_off_end_effector() -> Tuple[bool, dict]:
    """Powers off the end effector."""
    token = load_token()
    if not token:
        return False, {"error": "Cannot power off end effector without a control token."}
    url = f"{ROBOT_IP}/api/end-effector/power:off"
    headers = {"X-Control-Token": token}
    return _make_request("POST", url, headers=headers)

# ---------------- System ----------------

def reboot_system() -> Tuple[bool, dict]:
    url = f"{ROBOT_IP}/api/system:reboot"
    return _make_request("POST", url)

def shutdown_system() -> Tuple[bool, dict]:
    url = f"{ROBOT_IP}/api/system:shutdown"
    return _make_request("POST", url)

def get_operating_mode() -> Tuple[bool, dict]:
    url = f"{ROBOT_IP}/api/system/operating-mode"
    return _make_request("GET", url)

def switch_to_programming() -> Tuple[bool, dict]:
    token = load_token()
    if not token:
        return False, {"error": "Cannot switch mode without a control token."}
    url = f"{ROBOT_IP}/api/system/operating-mode:change"
    headers = {"X-Control-Token": token}
    body = {"desiredOperatingMode": "Programming"}
    
    # if not token:
    #     return False, {"error": "Cannot switch mode without a control token."}
    # url = f"{ROBOT_IP}/desk/api/operating-mode/programming"
    # headers = {"X-Control-Token": token}
    return _make_request("POST", url, headers=headers)

def switch_to_execution() -> Tuple[bool, dict]:
    token = load_token()
    if not token:
        return False, {"error": "Cannot switch mode without a control token."}
    url = f"{ROBOT_IP}/api/system/operating-mode:change"
    headers = {"X-Control-Token": token}
    body = {"desiredOperatingMode": "Execution"}
    return _make_request("POST", url, headers=headers, json=body)

# ---------------- Safety Self-Tests ----------------

def get_self_tests_status() -> Tuple[bool, dict]:
    url = f"{ROBOT_IP}/api/safety/self-tests"
    return _make_request("GET", url)

def execute_self_tests() -> Tuple[bool, dict]:
    token = load_token()
    if not token:
        return False, {"error": "Cannot execute self-tests without a control token."}
    url = f"{ROBOT_IP}/api/safety/self-tests:execute"
    headers = {"X-Control-Token": token}
    return _make_request("POST", url, headers=headers)
