# face_recognition_module.py

import os
import time
import random # Needed for random greetings if handled here
import face_recognition
import numpy as np # For argmin

# Import shared configurations and utilities
from . import config
from .utils import log_event
from .ai_core import speak_text # To trigger AI greetings from this module

# Global lists to store known face encodings and their corresponding names
known_face_encodings = []
known_face_names = []

# Global variables for recognition cooldown
_last_recognized_person = "None"
_last_recognition_time = 0

def load_known_faces():
    """
    Loads images from the KNOWN_FACES_DIR, encodes faces, and stores them.
    """
    global known_face_encodings, known_face_names # Declare globals
    print(f"[{time.strftime('%H:%M:%S')}] Loading known faces from '{config.KNOWN_FACES_DIR}'...")
    if not os.path.exists(config.KNOWN_FACES_DIR):
        print(f"[{time.strftime('%H:%M:%S')}] Warning: '{config.KNOWN_FACES_DIR}' directory not found. Face recognition will not work.")
        return

    for person_name in os.listdir(config.KNOWN_FACES_DIR):
        person_dir = os.path.join(config.KNOWN_FACES_DIR, person_name)
        if os.path.isdir(person_dir):
            for filename in os.listdir(person_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(person_dir, filename)
                    try:
                        image = face_recognition.load_image_file(image_path)
                        face_locations = face_recognition.face_locations(image)
                        if len(face_locations) > 0:
                            face_encoding = face_recognition.face_encodings(image, known_face_locations=face_locations)[0]
                            known_face_encodings.append(face_encoding)
                            known_face_names.append(person_name)
                            print(f"[{time.strftime('%H:%M:%S')}] Loaded face: {person_name} from {filename}")
                        else:
                            print(f"[{time.strftime('%H:%M:%S')}] Warning: No face found in {filename} for {person_name}. Skipping.")
                    except Exception as e:
                        print(f"[{time.strftime('%H:%M:%S')}] Error loading or encoding face from {image_path}: {e}")
    print(f"[{time.strftime('%H:%M:%S')}] Finished loading known faces. Total: {len(known_face_names)} faces.")

def recognize_faces_in_frame(rgb_frame):
    """
    Detects and recognizes faces in an RGB frame.
    Returns a list of (face_location, name) tuples.
    """
    global _last_recognized_person, _last_recognition_time

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    recognized_data = [] # List to store (face_location, name) for drawing

    current_time = time.time() # Get current time for cooldown checks

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        name = "Unknown"

        # Only attempt to match if there are known faces loaded
        if known_face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            best_match_index = np.argmin(face_distances) # Find the index of the best match
            if matches[best_match_index]: # If the best match is actually a 'match' (within tolerance)
                name = known_face_names[best_match_index]

        recognized_data.append(((top, right, bottom, left), name))

        # --- AI greeting based on recognized person ---
        if name != "Unknown" and name != _last_recognized_person and \
           (current_time - _last_recognition_time) > config.RECOGNITION_COOLDOWN_SECONDS:

            greeting_phrase_data = None
            if name == "nuba":
                greeting_phrase_data = {"text": random.choice(["Hello, Nuba!", "Is that Nuba?", "Hi, sweet Nuba!"]), "lang": "en"}
            elif name == "anmona":
                greeting_phrase_data = {"text": random.choice(["Hello, Anmona!", "Welcome, Anmona!", "Hi there, Anmona!"]), "lang": "en"}
            elif name == "dada":
                greeting_phrase_data = {"text": random.choice(["Hello, Dada!", "Good to see you, Dada!", "Hi, Dada!"]), "lang": "en"}

            if greeting_phrase_data:
                speak_text(greeting_phrase_data) # Call speak_text from ai_core
                log_event("Face_Recognition_Greeting", config.current_nuba_state, f"Greeted {name}: '{greeting_phrase_data['text']}' (Auto)")
                _last_recognized_person = name
                _last_recognition_time = current_time
        # --- End AI greeting ---

    return recognized_data