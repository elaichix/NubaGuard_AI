# main_app.py

import tkinter as tk
import threading
import os
import time

# Import modules
from . import config
from .utils import initialize_log_file, log_event
from .gui_app import NubaGuardGUI
from . import ai_core # Import ai_core to access its stop_listening_thread and listener_thread

if __name__ == "__main__":
    # Initialize the log file first
    initialize_log_file()
    log_event("System_Start", "N/A", "NubaGuard AI Assistant started")

    root = tk.Tk()
    app = NubaGuardGUI(root)

    try:
        root.mainloop()
    finally:
        # Ensure proper cleanup if GUI is closed or mainloop exits
        if hasattr(app, 'listener_thread') and app.listener_thread.is_alive():
            print(f"[{time.strftime('%H:%M:%S')}] Main loop exited. Signalling listener thread to stop.")
            ai_core.stop_listening_thread = True # Signal the thread in ai_core
            # Give the listener thread a chance to finish (max AI_LISTEN_DURATION + 2 seconds)
            app.listener_thread.join(timeout=config.AI_LISTEN_DURATION + 2) 
            if app.listener_thread.is_alive():
                print(f"[{time.strftime('%H:%M:%S')}] Warning: Listener thread did not terminate gracefully on mainloop exit.")
        log_event("System_Stop", config.current_nuba_state, "NubaGuard AI Assistant stopped gracefully")