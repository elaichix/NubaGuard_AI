# utils.py

import csv
import os
import time
# Remove email imports:
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

from . import config # Import config from the same package

# This global flag will be managed by the log_event function
_log_file_initialized = False

def log_event(event_type, nuba_state_for_log, details=""):
    """
    Logs an event to the CSV file.
    """
    global _log_file_initialized # Use the internal flag for this module

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_data = [timestamp, event_type, nuba_state_for_log, details]

    file_exists = os.path.exists(config.LOG_FILE)
    if not file_exists or os.path.getsize(config.LOG_FILE) == 0:
        _log_file_initialized = False # Ensure headers are written if file is new or empty

    with open(config.LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not _log_file_initialized:
            writer.writerow(config.LOG_HEADERS)
            _log_file_initialized = True
        writer.writerow(log_data)

def initialize_log_file():
    """
    Ensures the log file exists and has headers at startup.
    Should be called once at the beginning of the application.
    """
    if not os.path.exists(config.LOG_FILE) or os.path.getsize(config.LOG_FILE) == 0:
        with open(config.LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(config.LOG_HEADERS)
        print(f"[{time.strftime('%H:%M:%S')}] Initialized new log file: {config.LOG_FILE}")

# Remove email sending function:
# def send_email_alert(subject, body):
#     global config
#     
#     if not config.EMAIL_ALERTS_ENABLED:
#         print(f"[{time.strftime('%H:%M:%S')}] Email alerts are disabled in config.")
#         return
# 
#     current_time = time.time()
#     if (current_time - config.LAST_EMAIL_ALERT_TIME) < config.EMAIL_ALERT_COOLDOWN_SECONDS:
#         print(f"[{time.strftime('%H:%M:%S')}] Email alert cooldown active. Skipping email send.")
#         return
# 
#     try:
#         msg = MIMEMultipart()
#         msg['From'] = config.SENDER_EMAIL
#         msg['To'] = ", ".join(config.RECEIVER_EMAILS)
#         msg['Subject'] = subject
#         msg.attach(MIMEText(body, 'plain'))
# 
#         server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
#         server.starttls()
#         server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
#         server.sendmail(config.SENDER_EMAIL, config.RECEIVER_EMAILS, msg.as_string())
#         server.quit()
# 
#         config.LAST_EMAIL_ALERT_TIME = current_time
#         print(f"[{time.strftime('%H:%M:%S')}] Email alert sent: '{subject}' to {', '.join(config.RECEIVER_EMAILS)}")
#         log_event("Email_Alert_Sent", config.current_nuba_state, subject)
# 
#     except smtplib.SMTPAuthenticationError as e:
#         print(f"[{time.strftime('%H:%M:%S')}] SMTP Authentication Error: Check SENDER_EMAIL and SENDER_PASSWORD (or App Password). Error: {e}")
#         log_event("Email_Alert_Error", config.current_nuba_state, f"Authentication failed: {e}")
#     except smtplib.SMTPException as e:
#         print(f"[{time.strftime('%H:%M:%S')}] SMTP Error: Could not send email. Check SMTP_SERVER, SMTP_PORT, or internet connection. Error: {e}")
#         log_event("Email_Alert_Error", config.current_nuba_state, f"SMTP error: {e}")
#     except Exception as e:
#         print(f"[{time.strftime('%H:%M:%S')}] General Email Error: {e}")
#         log_event("Email_Alert_Error", config.current_nuba_state, f"General error: {e}")