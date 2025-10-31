# -*- coding: utf-8 -*-
"""
Created on Thu Sep 4 01:15:30 2025

@author: Lingyun

An automated script to maintain a Franka robot's operational status for long-running tasks.
It keeps the joints unlocked, FCI active, and handles the mandatory 24-hour self-test,
while also allowing for interactive keyboard commands and graceful shutdown from Docker.
"""
import time
import threading
import platform
import sys
import signal  # Added for signal handling
import config_loader

# Platform-specific imports for non-blocking keyboard input
if platform.system() == "Windows":
    import msvcrt
else:
    import tty
    import termios
    import select

# --- Load Configuration ---
config = config_loader.load_config()
k_config = config['keep_alive_settings']
import deskapi # Import after config is loaded to ensure it's initialized

CHECK_INTERVAL = k_config['check_interval_secs']
RETRY_DELAY = k_config['retry_delay_secs']
OWNER_NAME = k_config['owner_name']
SELF_TEST_TRIGGER_MINS = k_config['self_test_trigger_mins']
ACTION_ON_THRESHOLD = k_config['action_on_threshold']

# --- Global stop event for threads and signal handlers ---
stop_event = threading.Event()

def log_status(message):
    """Prints a message with a timestamp in a thread-safe manner."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)

def handle_self_test() -> bool:
    """
    Checks if a self-test is due or imminent and executes the configured action.
    Returns True if an action was successfully completed, False otherwise.
    """
    log_status("Checking self-test status...")
    success, data = deskapi.get_self_tests_status()
    if not success:
        log_status(f"  ERROR: Could not get self-test status: {data.get('error')}")
        return False

    status = data.get('status')
    remaining_secs = data.get('remaining')
    
    if remaining_secs is not None:
        log_status(f"  Self-test status is '{status}'. Time remaining: {remaining_secs // 60} mins.")
    else:
        log_status(f"  Self-test status is '{status}'.")

    action_needed = False
    if status == 'Elapsed':
        log_status("!!! Self-test is overdue. Action is required. !!!")
        action_needed = True
    elif status in ['OK', 'Warning'] and remaining_secs is not None:
        if remaining_secs <= (SELF_TEST_TRIGGER_MINS * 60):
            log_status(f"!!! Remaining time ({remaining_secs // 60} mins) is below threshold ({SELF_TEST_TRIGGER_MINS} mins). Action is required. !!!")
            action_needed = True

    if not action_needed:
        return False

    log_status(f"  Preparing to perform configured action: '{ACTION_ON_THRESHOLD}'")
    run_deactivate_routine(is_manual=False)

    if ACTION_ON_THRESHOLD == 'reboot':
        log_status("  Initiating system reboot...")
        s_reboot, r_reboot = deskapi.reboot_system()
        if s_reboot:
            log_status("  SUCCESS: Reboot command sent. The script will now exit.")
            stop_event.set() # Use stop_event to exit gracefully
        else:
            log_status(f"  ERROR: Failed to send reboot command: {r_reboot.get('error')}")
            return False

    elif ACTION_ON_THRESHOLD == 'self-test':
        log_status("  Taking control to run self-test...")
        s_ctrl, r_ctrl = deskapi.enforce_control(owner=OWNER_NAME)
        if not s_ctrl:
            log_status(f"  ERROR: Could not take control to run self-test: {r_ctrl.get('error')}")
            return False

        log_status("  Executing self-tests... This may take a few minutes.")
        s_test, r_test = deskapi.execute_self_tests()
        if s_test:
            log_status("  SUCCESS: Self-test executed successfully.")
            deskapi.release_control()
            return True
        else:
            log_status(f"  ERROR: Self-test execution failed: {r_test.get('error')}")
            deskapi.release_control()
            return False
    else:
        log_status(f"  ERROR: Unknown ACTION_ON_THRESHOLD '{ACTION_ON_THRESHOLD}'. No action taken.")
        return False

def ensure_robot_ready():
    """Checks the robot's state and takes action to make it ready."""
    log_status("Ensuring robot is in a ready state...")
    s_ctrl, d_ctrl = deskapi.get_control_status()
    if not s_ctrl or d_ctrl.get('owner') != OWNER_NAME:
        log_status(f"  Control not held by '{OWNER_NAME}'. Taking control...")
        s, r = deskapi.enforce_control(owner=OWNER_NAME)
        if not s:
            log_status(f"  ERROR: Failed to take control: {r.get('error')}. Retrying after delay.")
            time.sleep(RETRY_DELAY)
            return False, {'error': r.get('error')}
    else:
        log_status("  Control token is correctly held.")

    s_joints, d_joints = deskapi.get_joint_states()
    if s_joints and d_joints.get('status') == 'Locked':
        log_status("  Joints are locked. Unlocking...")
        s, r = deskapi.unlock_joints()
        if not s:
            log_status(f"  ERROR: Failed to unlock joints: {r.get('error')}. Retrying after delay.")
            time.sleep(RETRY_DELAY)
            return False, {'error': r.get('error')}
    elif not s_joints:
         log_status(f"  ERROR: Could not get joint status: {d_joints.get('error')}")
    else:
        log_status(f"  Joint status is '{d_joints.get('status')}'.")

    # --- New End Effector Power Check ---
    s_ee, d_ee = deskapi.get_end_effector_power_status()
    if s_ee and d_ee.get('status') == 'Off':
        log_status("  End Effector is Off. Attempting to power on...")
        s_ee_on, r_ee_on = deskapi.power_on_end_effector()
        if not s_ee_on:
            log_status(f"  WARNING: Failed to power on End Effector: {r_ee_on.get('error')}. Gripper (FrankaHand) may not be connected.")
        else:
            log_status("  End Effector powered On.")
    elif not s_ee:
        log_status(f"  WARNING: Could not get End Effector power status: {d_ee.get('error')}. Gripper status unknown.")
    else:
        log_status(f"  End Effector is {d_ee.get('status', 'Unknown')}.")
    # --- End of New Check ---

    s_fci, d_fci = deskapi.get_fci_status()
    if s_fci and d_fci.get('status') == 'Inactive':
        log_status("  FCI is inactive. Activating...")
        s, r = deskapi.activate_fci()
        if not s:
            log_status(f"  ERROR: Failed to activate FCI: {r.get('error')}. Retrying after delay.")
            time.sleep(RETRY_DELAY)
            return False, {'error': r.get('error')}
    elif not s_fci:
        log_status(f"  ERROR: Could not get FCI status: {d_fci.get('error')}")
    else:
        log_status("  FCI is Active.")
    
    log_status("Robot is ready.")
    return True, d_ee

def run_deactivate_routine(is_manual=True):
    """Safely deactivates the robot (Routine 2)."""
    if is_manual:
        log_status("--- MANUAL ACTION: Deactivating Robot ---")
    else:
        log_status("--- Deactivating Robot ---")
        
    log_status("  Deactivating FCI...")
    deskapi.deactivate_fci()
    time.sleep(1)
    log_status("  Locking joints...")
    deskapi.lock_joints()
    time.sleep(1)
    log_status("  Powering off End Effector...")
    deskapi.power_off_end_effector()
    time.sleep(1)
    log_status("  Releasing control token...")
    deskapi.release_control()
    
    if is_manual:
        log_status("--- MANUAL ACTION: Deactivation complete ---")
    else:
        log_status("--- Deactivation complete ---")


def automated_loop():
    """The main automated loop, runs in a background thread."""
    while not stop_event.is_set():
        try:
            action_was_taken = handle_self_test()
            if action_was_taken:
                log_status("A maintenance action was performed. Waiting for robot to settle before next check.")
                # Use a loop to check the stop_event frequently
                for _ in range(CHECK_INTERVAL):
                    if stop_event.is_set():
                        break
                    time.sleep(1)
                continue

            ensure_robot_ready()

            log_status(f"--- Check complete. Waiting {CHECK_INTERVAL} seconds. ---")
            for _ in range(CHECK_INTERVAL):
                if stop_event.is_set():
                    break
                time.sleep(1)

        except Exception as e:
            log_status(f"An unexpected error occurred in automated loop: {e}")
            log_status(f"Waiting for {RETRY_DELAY} seconds before continuing.")
            time.sleep(RETRY_DELAY)

# --- New Function: Signal Handler ---
def graceful_shutdown_handler(signum, frame):
    """Handles SIGTERM from Docker, ensuring a clean shutdown."""
    if not stop_event.is_set():
        log_status(f"\n--- SIGNAL {signal.Signals(signum).name} DETECTED: Initiating Graceful Shutdown ---")
        run_deactivate_routine(is_manual=False)
        log_status("Robot deactivated. Exiting.")
        stop_event.set()

def main():
    """Main loop for the keep-alive script with interactive keyboard controls."""
    log_status("--- Starting Robot Keep-Alive Script ---")
    log_status(f"Configuration loaded from '{config_loader.CONFIG_FILE}'")
    
    # --- Register Signal Handlers ---
    signal.signal(signal.SIGTERM, graceful_shutdown_handler)
    signal.signal(signal.SIGINT, graceful_shutdown_handler) # Also handle Ctrl+C via signal
    
    auto_thread = threading.Thread(target=automated_loop, daemon=True)
    auto_thread.start()

    log_status("\n--- INTERACTIVE MODE ENABLED ---")
    log_status("Press 'd' to deactivate, 's' to shutdown, 'r' to reboot, 'q' to quit.")
    
    try:
        if platform.system() == "Windows":
            while not stop_event.is_set():
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    handle_key_press(key)
                time.sleep(0.1)
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                while not stop_event.is_set():
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        handle_key_press(key)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
    except Exception as e:
        # This will likely not be reached due to signal handlers, but is good practice
        log_status(f"An error occurred in the main input loop: {e}")
    finally:
        if not stop_event.is_set():
             # This block will run if the loop exits for a reason other than a signal
             log_status("Main loop exited unexpectedly. Cleaning up.")
             graceful_shutdown_handler("UNEXPECTED_EXIT", None)
        
        log_status("Waiting for background thread to finish...")
        auto_thread.join(timeout=5.0)
        log_status("Exiting.")

def handle_key_press(key: str):
    """Handles user key presses for manual actions."""
    if stop_event.is_set():
        return # Ignore key presses during shutdown
        
    if key == 'd':
        run_deactivate_routine()
    elif key == 's':
        log_status("--- MANUAL ACTION: Shutting Down Robot ---")
        run_deactivate_routine()
        deskapi.shutdown_system()
        log_status("Shutdown command sent. Exiting script.")
        stop_event.set()
    elif key == 'r':
        log_status("--- MANUAL ACTION: Rebooting Robot ---")
        run_deactivate_routine()
        deskapi.reboot_system()
        log_status("Reboot command sent. Exiting script.")
        stop_event.set()
    elif key == 'q':
        log_status("--- MANUAL ACTION: Quitting Script ---")
        run_deactivate_routine()
        log_status("Robot deactivated. Exiting.")
        stop_event.set()

#if __name__ == "__main__":
#    main()