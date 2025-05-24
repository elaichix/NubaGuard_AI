# ai_core.py

import time
import random
import os
import soundfile as sf
import numpy as np

import librosa
from sklearn.preprocessing import StandardScaler

import speech_recognition as sr
import threading

from gtts import gTTS
from playsound import playsound

import google.generativeai as genai

from . import config
from .utils import log_event

genai.configure(api_key=config.GEMINI_API_KEY)
gemini_model_instance = genai.GenerativeModel(config.GEMINI_MODEL_NAME)

recognized_speech_text = None
speech_lock = threading.Lock()
stop_listening_thread = False

current_detected_objects = "" # Will be a comma-separated string of object labels

_last_cry_alert_time = 0

def speak_text(text_data, filename=config.AI_SPEECH_FILENAME):
    if isinstance(text_data, dict):
        text = text_data['text']
        lang = text_data['lang']
    else:
        text = text_data
        lang = config.AI_SPEECH_LANG

    print(f"[{time.strftime('%H:%M:%S')}] AI is synthesizing: '{text}' (lang: {lang})...")
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filename)
        playsound(filename, block=False)
        print(f"[{time.strftime('%H:%M:%S')}] AI is speaking...")
        log_event("AI_Speech", config.current_nuba_state, f"'{text}' (lang: {lang})")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error during AI speech generation or playback: {e}")
        log_event("AI_Speech_Error", config.current_nuba_state, f"'{text}' (lang: {lang}) - {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def analyze_audio_for_cry(audio_file_path):
    try:
        y, sr = librosa.load(audio_file_path, sr=None)

        rms = librosa.feature.rms(y=y)[0]
        avg_rms = np.mean(rms)

        cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        avg_cent = np.mean(cent)

        f0, voiced_flag, voiced_probs = librosa.pyin(y=y, sr=sr, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        f0 = f0[voiced_flag]
        
        pitch_variance = 0
        if len(f0) > 1:
            f0_semitones = 12 * np.log2(f0 / 100.0 + 1e-10)
            pitch_variance = np.var(f0_semitones)

        print(f"[{time.strftime('%H:%M:%S')}] Audio analysis: RMS={avg_rms:.4f}, Centroid={avg_cent:.1f}Hz, PitchVar={pitch_variance:.1f}")

        is_cry = (avg_rms > config.CRY_RMS_THRESHOLD and
                  avg_cent > config.CRY_SPECTRAL_CENTROID_THRESHOLD and
                  pitch_variance > config.CRY_PITCH_VARIANCE_THRESHOLD)
        
        if is_cry:
            print(f"[{time.strftime('%H:%M:%S')}] Detected potential cry based on audio features.")

        return is_cry
    
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error during audio cry analysis: {e}")
        return False

def listen_in_background(recognizer):
    global recognized_speech_text, stop_listening_thread, _last_cry_alert_time

    print(f"[{time.strftime('%H:%M:%S')}] Background listener: Adjusting for ambient noise...")
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    print(f"[{time.strftime('%H:%M:%S')}] Background listener: Microphone calibrated.")

    while not stop_listening_thread:
        with sr.Microphone() as source:
            current_time = time.time()
            with speech_lock:
                recognized_speech_text = None
                
            try:
                audio_data = recognizer.listen(source, timeout=config.AI_LISTEN_DURATION, phrase_time_limit=config.AI_LISTEN_DURATION)
                
                with open(config.CRY_AUDIO_TEMP_FILE, "wb") as f:
                    f.write(audio_data.get_wav_data())

                is_cry = analyze_audio_for_cry(config.CRY_AUDIO_TEMP_FILE)
                if is_cry:
                    if (current_time - _last_cry_alert_time) > config.CRY_ALERT_COOLDOWN_SECONDS:
                        print(f"[{time.strftime('%H:%M:%S')}] !!! CRY DETECTED !!!")
                        log_event("Cry_Detected", config.current_nuba_state, "Likely crying detected by audio analysis")
                        speak_text({"text": "Oh, Nuba is crying! Mama is coming!", "lang": "en"})
                        _last_cry_alert_time = current_time
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] Cry detected, but still in cooldown.")
                
                text = recognizer.recognize_google(audio_data, language="en-US")
                
                with speech_lock:
                    recognized_speech_text = text
                print(f"[{time.strftime('%H:%M:%S')}] Background listener heard (for STT): \"{text}\"")

            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                print(f"[{time.strftime('%H:%M:%S')}] Background listener: Could not understand audio for STT.")
            except sr.RequestError as e:
                print(f"[{time.strftime('%H:%M:%S')}] Background listener: Could not request results from Google SR service; {e}")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Background listener: An unexpected error occurred: {e}")
            finally:
                if os.path.exists(config.CRY_AUDIO_TEMP_FILE):
                    os.remove(config.CRY_AUDIO_TEMP_FILE)
                
            time.sleep(1)

# --- MODIFIED: get_gemini_response for object_context (Day 24) ---
def get_gemini_response(prompt_text, object_context=""):
    # Removed 'global' keyword from here:
    # global config.LAST_GEMINI_CALL_TIME # Access global from config 

    current_time = time.time()
    if (current_time - config.LAST_GEMINI_CALL_TIME) < config.GEMINI_COOLDOWN_SECONDS:
        print(f"[{time.strftime('%H:%M:%S')}] Gemini cooldown active. Skipping API call.")
        return "I need a little rest, Nuba! Let's talk soon."

    try:
        context_instruction = ""
        if object_context:
            context_instruction = f"I see the following objects nearby: {object_context}. "
        
        system_instruction = (
            f"You are 'NubaGuard', a kind, gentle, and very playful AI friend for an 8-month-old baby named Nuba. "
            f"Your goal is to engage and comfort her. "
            f"Your responses MUST be extremely short (1-5 words maximum), simple, and very positive. "
            f"Use simple baby-friendly vocabulary. "
            f"If Nuba babbles or makes unclear sounds, respond with gentle encouragement, a playful sound (like 'coo' or 'boop'), or a simple question. "
            f"Never ask complex questions or give long explanations. "
            f"If Nuba's speech appears to be English, respond in English. If it appears to be Bengali (like 'Ma', 'Baba', or common Bengali babbling), respond in simple Bengali. "
            f"You can refer to Nuba directly. Current Nuba's state is {config.current_nuba_state}. "
            f"{context_instruction}" # <-- Inject object context here
            f"Always prioritize Nuba's happiness and safety."
        )

        chat_session = gemini_model_instance.start_chat(history=[])
        
        response = chat_session.send_message(f"System: {system_instruction}\nUser: {prompt_text}")
        
        config.LAST_GEMINI_CALL_TIME = current_time # Update last call time upon successful request

        if response and response.text:
            return response.text
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Gemini response was empty or malformed.")
            return "Hmm, I'm not sure what to say, Nuba."

    except genai.types.BlockedPromptException as e:
        print(f"[{time.strftime('%H:%M:%S')}] Gemini blocked prompt: {e.response.prompt_feedback}")
        return "I can't respond to that right now, Nuba."
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error getting Gemini response: {e}")
        return "Oops, something went wrong, Nuba."