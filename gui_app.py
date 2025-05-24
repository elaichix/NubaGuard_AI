# gui_app.py

import cv2
import time
import tkinter as tk
from PIL import Image, ImageTk
import threading
import speech_recognition as sr
import random
from playsound import playsound

import face_recognition # Keep this for face_recognition.face_locations etc.

from . import config
from .utils import log_event

from . import ai_core
from .ai_core import speak_text

# --- MODIFIED IMPORT HERE ---
from .face_recognition_module import ( # <-- Use this to import specific items
    load_known_faces,
    recognize_faces_in_frame,
    known_face_encodings,      # <-- Import the global lists/variables directly
    known_face_names,          # <-- Import the global lists/variables directly
    _last_recognized_person,   # <-- Import the global variable directly
    _last_recognition_time     # <-- Import the global variable directly
)
# --- END MODIFIED IMPORT ---

from . import object_detection_module


class NubaGuardGUI:
    def __init__(self, master):
        self.master = master
        master.title("NubaGuard AI Assistant")
        master.geometry("800x700")

        self.state_label = tk.Label(master, text=f"Nuba State: {config.current_nuba_state.upper()}", font=("Arial", 24), fg="blue")
        self.state_label.pack(pady=10)

        self.video_frame = tk.Frame(master, width=640, height=480, bg="black")
        self.video_frame.pack()
        self.canvas = tk.Label(self.video_frame)
        self.canvas.pack()

        self.control_frame = tk.Frame(master)
        self.control_frame.pack(pady=10)

        self.say_hello_button = tk.Button(self.control_frame, text="Say Hello (EN)", command=lambda: speak_text({"text": "Hello Nuba!", "lang": "en"}))
        self.say_hello_button.grid(row=0, column=0, padx=5, pady=2)

        self.say_play_button = tk.Button(self.control_frame, text="Suggest Play (EN)", command=lambda: speak_text({"text": "Want to play, Nuba?", "lang": "en"}))
        self.say_play_button.grid(row=0, column=1, padx=5, pady=2)

        self.say_kemon_acho_button = tk.Button(self.control_frame, text="কেমন আছো নূবা? (BN)", command=lambda: speak_text({"text": "কেমন আছো নূবা?", "lang": "bn"}))
        self.say_kemon_acho_button.grid(row=1, column=0, padx=5, pady=2)

        self.say_kanna_button = tk.Button(self.control_frame, text="কান্না কেন? (BN)", command=lambda: speak_text({"text": "নূবা, কান্না করছো কেন?", "lang": "bn"}))
        self.say_kanna_button.grid(row=1, column=1, padx=5, pady=2)

        self.say_anmona_button = tk.Button(self.control_frame, text="Hello Anmona (EN)", command=lambda: speak_text({"text": "Hello Anmona! How are you?", "lang": "en"}))
        self.say_anmona_button.grid(row=2, column=0, padx=5, pady=2)

        self.say_dada_button = tk.Button(self.control_frame, text="Hello Dada (EN)", command=lambda: speak_text({"text": "Hello Dada! Nuba is so happy you are here.", "lang": "en"}))
        self.say_dada_button.grid(row=2, column=1, padx=5, pady=2)

        self.quit_button = tk.Button(self.control_frame, text="Quit", command=self.on_closing, bg="red", fg="white")
        self.quit_button.grid(row=0, column=3, rowspan=3, padx=5, sticky="ns")

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera for GUI.")
            log_event("System_Error", "N/A", "Camera not opened for GUI")
            master.destroy()
            return

        self.previous_frame = None
        self.motion_start_time = None
        self.last_motion_time = time.time()
        self.alert_triggered_by_motion = False
        self.ai_greeted_nuba_on_wake = False
        self.last_ai_speech_time = 0
        self.ai_said_goodnight = False

        self.recognizer = sr.Recognizer()
        self.listener_thread = threading.Thread(target=ai_core.listen_in_background, args=(self.recognizer,))
        self.listener_thread.daemon = True
        self.listener_thread.start()
        print(f"[{time.strftime('%H:%M:%S')}] Listening thread started from GUI.")
        log_event("STT_Thread_Start", "N/A", "Speech recognition thread initiated by GUI")

        load_known_faces() # Call load_known_faces (it's directly imported)
        object_detection_module.load_yolo_model()

        self.update_video_feed()
        
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_video_feed(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            log_event("System_Error", config.current_nuba_state, "Failed to read camera frame in GUI")
            self.master.after(10, self.update_video_feed)
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # --- Face Detection and Recognition ---
        # Calls to functions from face_recognition_module
        recognized_faces_data = recognize_faces_in_frame(rgb_frame) 
        
        # Loop through each recognized face to draw on screen
        for (top, right, bottom, left), name in recognized_faces_data:
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # Inside the GUI, you need to trigger the greeting action
            # The actual greeting logic (speak_text, log_event, updating _last_recognized_person)
            # is now handled within face_recognition_module.recognize_faces_in_frame
            # because that function knows who was recognized and when.
            # So, you don't need the if/else block for greetings here anymore.
            # The recognize_faces_in_frame function in face_recognition_module.py
            # will internally call speak_text and log_event if a greeting is due.

        # --- End Face Detection and Recognition ---


        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        if self.previous_frame is None:
            self.previous_frame = gray_frame.copy()
            self.master.after(10, self.update_video_feed)
            return


        frame_delta = cv2.absdiff(self.previous_frame, gray_frame)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        significant_motion_found = False
        for contour in contours:
            if cv2.contourArea(contour) < 800:
                continue
            significant_motion_found = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        current_time = time.time()

        if significant_motion_found:
            if current_time - self.last_motion_time > 0:
                log_event("Motion_Detected", config.current_nuba_state, f"Motion resumed after {(current_time - self.last_motion_time):.2f}s stillness")
            self.last_motion_time = current_time
            self.ai_said_goodnight = False 

        if significant_motion_found:
            if self.motion_start_time is None:
                self.motion_start_time = current_time
                print(f"[{time.strftime('%H:%M:%S')}] Minor motion detected. Waiting for sustained movement...")
                log_event("Motion_Start", config.current_nuba_state, "Minor motion detected, starting timer")

            if current_time - self.motion_start_time >= config.MOTION_DURATION_THRESHOLD:
                if config.current_nuba_state == "sleeping":
                    old_state = config.current_nuba_state
                    config.current_nuba_state = "awake/moving"
                    print(f"[{time.strftime('%H:%M:%S')}] Nuba state changed from {old_state} to {config.current_nuba_state.upper()}")
                    self.alert_triggered_by_motion = True
                    print(f"[{time.strftime('%H:%M:%S')}] !!! ALERT: Nuba is awake and moving! !!!")
                    print("Consider checking on Nuba now.")
                    log_event("Nuba_Woke_Up", config.current_nuba_state, "Nuba transitioned to awake/moving")
                    
                    try:
                        playsound(config.ALERT_SOUND_FILE, block=False)
                        print(f"[{time.strftime('%H:%M:%S')}] Playing alert sound: {config.ALERT_SOUND_FILE}")
                        log_event("Alert_Sound", config.current_nuba_state, "Played alert chime")
                    except Exception as e:
                        print(f"[{time.strftime('%H:%M:%S')}] Error playing alert sound: {e}")
                        log_event("Alert_Sound_Error", config.current_nuba_state, str(e))
                    
                    if not self.ai_greeted_nuba_on_wake:
                        phrase_data = random.choice(config.NUBA_PLAY_PHRASES)
                        speak_text(phrase_data)
                        self.ai_greeted_nuba_on_wake = True
                        self.last_ai_speech_time = current_time
                
                if config.current_nuba_state == "awake/moving" and (current_time - self.last_ai_speech_time) >= config.AI_SPEAK_INTERVAL:
                    print(f"[{time.strftime('%H:%M:%S')}] AI is ready to speak again (interval met). Time since last speech: {current_time - self.last_ai_speech_time:.2f}s (Interval: {config.AI_SPEAK_INTERVAL}s)")
                    phrase_data = random.choice(config.NUBA_PLAY_PHRASES)
                    speak_text(phrase_data)
                    self.last_ai_speech_time = current_time
                
                with ai_core.speech_lock:
                    if ai_core.recognized_speech_text:
                        detected_phrase = ai_core.recognized_speech_text
                        print(f"[{time.strftime('%H:%M:%S')}] Main loop detected recognized speech: \"{detected_phrase}\"")
                        log_event("STT_Recognition", config.current_nuba_state, f"Heard: {detected_phrase}")
                        
                        gemini_response_text = ai_core.get_gemini_response(
                            detected_phrase, 
                            object_context=ai_core.current_detected_objects
                        )
                        
                        if gemini_response_text:
                            speak_text({"text": gemini_response_text, "lang": config.AI_SPEECH_LANG}) 
                        else:
                            speak_text("I'm not sure what to say, Nuba!", lang=config.AI_SPEECH_LANG)
                        
                        ai_core.recognized_speech_text = None
            else:
                 if self.motion_start_time is not None and (current_time - self.last_motion_time) > config.MOTION_DURATION_THRESHOLD:
                     self.motion_start_time = None
        else:
            if config.current_nuba_state == "awake/moving" and (current_time - self.last_motion_time) >= config.INACTIVITY_SLEEP_THRESHOLD:
                if self.alert_triggered_by_motion:
                    print(f"[{time.strftime('%H:%M:%S')}] Nuba has settled down. Initiating sleep detection.")
                    log_event("Nuba_Settled", config.current_nuba_state, "Nuba settled after activity")
                
                old_state = config.current_nuba_state
                config.current_nuba_state = "sleeping"
                print(f"[{time.strftime('%H:%M:%S')}] Nuba state changed from {old_state} to {config.current_nuba_state.upper()}")
                self.alert_triggered_by_motion = False
                self.ai_greeted_nuba_on_wake = False
                self.last_ai_speech_time = 0
                
                if not self.ai_said_goodnight:
                    print(f"[{time.strftime('%H:%M:%S')}] Confirmed Nuba is likely sleeping. Good night, Nuba!")
                    log_event("Nuba_Asleep", config.current_nuba_state, "Nuba detected as asleep")
                    speak_text({"text": "Good night, Nuba. Sweet dreams.", "lang": "en"})
                    self.ai_said_goodnight = True
            
            self.motion_start_time = None

        self.previous_frame = gray_frame.copy()

        self.state_label.config(text=f"Nuba State: {config.current_nuba_state.upper()}")

        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.imgtk = imgtk
        self.canvas.config(image=imgtk)

        self.master.after(10, self.update_video_feed)

    def on_closing(self):
        ai_core.stop_listening_thread = True
        self.cap.release()
        self.master.destroy()
        print(f"[{time.strftime('%H:%M:%S')}] NubaGuard GUI closed.")
        log_event("System_Stop", config.current_nuba_state, "NubaGuard AI Assistant stopped via GUI")
        
        if hasattr(self, 'listener_thread') and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=config.AI_LISTEN_DURATION + 2)
            if self.listener_thread.is_alive():
                print(f"[{time.strftime('%H:%M:%S')}] Warning: Listener thread did not terminate gracefully. It might be waiting for microphone input.")