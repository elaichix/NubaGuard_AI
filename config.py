# config.py

import os
import time

# --- Gemini API Configuration ---
GEMINI_API_KEY = "Your API Key" # Your actual API key
GEMINI_MODEL_NAME = 'models/gemini-1.5-pro' # As per your successful debug

# --- Global Variables for Cooldowns (shared across modules) ---
LAST_GEMINI_CALL_TIME = 0
GEMINI_COOLDOWN_SECONDS = 5 # Reduced cooldown as billing is active

# --- Configuration for Alerts ---
ALERT_SOUND_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert_chime.wav")
MOTION_DURATION_THRESHOLD = 2.0 # Can be adjusted after debugging

# --- Configuration for AI Voice ---
AI_SPEECH_FILENAME = "nuba_ai_speech.mp3" # Temporary file for AI's speech
AI_SPEECH_LANG = 'en' # Default language for AI's speech

NUBA_PLAY_PHRASES = [
    {"text": "Hello Nuba. Are you awake now?", "lang": "en"},
    {"text": "Peek-a-boo! I see you!", "lang": "en"},
    {"text": "Are you happy, little one?", "lang": "en"},
    {"text": "Let's play!", "lang": "en"},
    {"text": "What are you looking at?", "lang": "en"},
    {"text": "I'm here with you, Nuba.", "lang": "en"},
    {"text": "Such a smart girl!", "lang": "en"},
    {"text": "Coochie coo!", "lang": "en"},
    {"text": "Time to explore!", "lang": "en"},
    {"text": "Are you feeling playful?", "lang": "en"},
    {"text": "কেমন আছো নূবা?", "lang": "bn"},
    {"text": "নূবা, কান্না করছো কেন?", "lang": "bn"},
    {"text": "তোমার বাবা আসছে এখন।", "lang": "bn"},
    {"text": "তোমার মাকে ডাকো। আম্মা।", "lang": "bn"},
    {"text": "মা বাবা ডাকো তো।", "lang": "bn"}
]
AI_SPEAK_INTERVAL = 10

# --- Configuration for AI Listening ---
AI_LISTEN_INTERVAL = 15
AI_LISTEN_DURATION = 3

# --- Keyword Responses (Mostly replaced by Gemini, but can be a fallback/direct trigger) ---
KEYWORD_RESPONSES = {
    "play": {"text": "Let's have some fun, Nuba!", "lang": "en"},
    "mama": {"text": "Mama loves you very much, Nuba!", "lang": "en"},
    "dada": {"text": "Dada is thinking of you, Nuba!", "lang": "en"},
    "yes": {"text": "That's great! Tell me more.", "lang": "en"},
    "no": {"text": "It's okay, Nuba. What do you like?", "lang": "en"},
    "love": {"text": "I love you too, Nuba!", "lang": "en"},
    "baby": {"text": "Yes, you are my sweet little baby!", "lang": "en"},
    "smile": {"text": "I hope you are smiling, Nuba!", "lang": "en"},
    "মা": {"text": "হ্যাঁ নূবা, মা তোমার পাশেই আছে।", "lang": "bn"}
}

# --- Configuration for Sleep Detection ---
INACTIVITY_SLEEP_THRESHOLD = 15
SLEEP_SOUND_FILE = "good_night_nuba.mp3" # Or use a gTTS phrase

# --- Configuration for Data Logging ---
LOG_FILE = "nuba_activity_log.csv"
LOG_HEADERS = ["Timestamp", "Event_Type", "Nuba_State", "Details"]

# --- Face Recognition Configuration ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR = os.path.join(_current_dir, "known_faces")
RECOGNITION_COOLDOWN_SECONDS = 15

# --- Cry Detection Configuration ---
CRY_AUDIO_TEMP_FILE = os.path.join(_current_dir, "temp_cry_audio.wav")
CRY_SPECTRAL_CENTROID_THRESHOLD = 2500
CRY_RMS_THRESHOLD = 0.02
CRY_PITCH_VARIANCE_THRESHOLD = 150
CRY_ALERT_COOLDOWN_SECONDS = 30

# --- Object Detection Configuration (New for Day 23) ---
MODEL_DATA_DIR = os.path.join(_current_dir, "model_data")
YOLO_WEIGHTS = os.path.join(MODEL_DATA_DIR, "yolov3-tiny.weights")
YOLO_CONFIG = os.path.join(MODEL_DATA_DIR, "yolov3-tiny.cfg")
COCO_NAMES = os.path.join(MODEL_DATA_DIR, "coco.names")

YOLO_CONFIDENCE_THRESHOLD = 0.5 # Minimum confidence to detect an object
YOLO_NMS_THRESHOLD = 0.3      # Non-maximum suppression threshold

# Pre-load YOLO classes
YOLO_CLASSES = []
if os.path.exists(COCO_NAMES):
    with open(COCO_NAMES, 'r') as f:
        YOLO_CLASSES = [line.strip() for line in f.readlines()]
else:
    print(f"[{time.strftime('%H:%M:%S')}] Warning: {COCO_NAMES} not found. Object detection class names will be missing.")
    YOLO_CLASSES = [f"Class {i}" for i in range(80)] # Fallback names

# --- Global variable for Nuba's state (managed in GUI, but accessible globally) ---
current_nuba_state = "sleeping"

# --- Email Notification Configuration (Removed for now as per user request) ---
# EMAIL_ALERTS_ENABLED = True
# SENDER_EMAIL = "your_sending_email@gmail.com"
# SENDER_PASSWORD = "your_app_password"
# RECEIVER_EMAILS = ["anmona_email@example.com", "your_email@example.com"]
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# LAST_EMAIL_ALERT_TIME = 0
# EMAIL_ALERT_COOLDOWN_SECONDS = 60
# --- End Email Notification Configuration ---