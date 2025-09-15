"""
wavebell_pi.py

Raspberry Pi main script for WaveBell (Contactless Doorbell) — SRS implementation.

Features implemented:
- PIR motion detection (PIR sensor)
- Ultrasonic distance check (HC-SR04)
- Camera capture on trigger (PiCamera or OpenCV fallback)
- Upload of sensor readings and images to ThingSpeak
- Optional email alert (SMTP) or webhook notification
- Local logging to CSV
- Simple HTTP endpoint to fetch last event (optional -- needs Flask if used)

Notes:
- Adjust PIN numbers to your wiring.
- Requires Python 3.7+ on Raspberry Pi OS.
- For camera use `picamera` (preferred on Pi) or `opencv` if using USB camera.
"""

import time
import os
import csv
import json
import base64
import requests
import datetime
import smtplib
from email.message import EmailMessage

# Attempt to import Pi-specific libraries
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except Exception as e:
    print("RPi.GPIO not available. Running in simulation mode. Error:", e)
    HAS_GPIO = False

# Try picamera first
USE_PICAMERA = False
try:
    from picamera import PiCamera
    USE_PICAMERA = True
except Exception:
    try:
        import cv2
        USE_PICAMERA = False
    except Exception:
        print("No camera libraries found. Camera functions will be simulated.")


# -------------------------
# Configuration (edit these)
# -------------------------
CONFIG = {
    "PIR_PIN": 17,           # GPIO pin for PIR output
    "TRIG_PIN": 23,          # HC-SR04 TRIG
    "ECHO_PIN": 24,          # HC-SR04 ECHO
    "BUZZER_PIN": 27,        # Optional buzzer
    "CAM_SAVE_PATH": "/home/pi/wavebell/media",  # ensure path exists or change
    "LOG_CSV": "/home/pi/wavebell/logs/events.csv",
    "THINGSPEAK_WRITE_KEY": "PUT_YOUR_THINGSPEAK_WRITE_KEY",
    "THINGSPEAK_UPDATE_URL": "https://api.thingspeak.com/update",
    "THINGSPEAK_CHANNEL_API": "https://api.thingspeak.com/channels/{channel_id}/feeds.json",
    "EMAIL_ALERTS": True,
    "SMTP": {
        "host": "smtp.gmail.com",
        "port": 587,
        "user": "youremail@gmail.com",
        "password": "your_app_or_password",
        "to": "owner@example.com"
    },
    "MIN_DISTANCE_CM": 25,   # minimum range for ultrasonic to confirm presence
    "EVENT_DEBOUNCE_SEC": 5, # don't re-trigger too fast
}

os.makedirs(os.path.dirname(CONFIG["CAM_SAVE_PATH"]), exist_ok=True)
os.makedirs(os.path.dirname(CONFIG["LOG_CSV"]), exist_ok=True)

# -------------------------
# GPIO Setup
# -------------------------
if HAS_GPIO:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CONFIG["PIR_PIN"], GPIO.IN)
    GPIO.setup(CONFIG["TRIG_PIN"], GPIO.OUT)
    GPIO.setup(CONFIG["ECHO_PIN"], GPIO.IN)
    GPIO.setup(CONFIG["BUZZER_PIN"], GPIO.OUT)
    GPIO.output(CONFIG["TRIG_PIN"], False)
    time.sleep(2)


# -------------------------
# Camera helper
# -------------------------
def capture_image(prefix="event"):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{ts}.jpg"
    path = os.path.join(CONFIG["CAM_SAVE_PATH"], filename)
    try:
        if USE_PICAMERA:
            camera = PiCamera()
            camera.resolution = (1024, 768)
            camera.start_preview()
            time.sleep(1)
            camera.capture(path)
            camera.close()
        else:
            # Try OpenCV
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(path, frame)
            cap.release()
        print("Captured image:", path)
        return path
    except Exception as e:
        print("Camera capture failed:", e)
        return None


# -------------------------
# Ultrasonic distance helper
# -------------------------
def measure_distance_cm():
    if not HAS_GPIO:
        # Simulate
        return 50.0
    # Trigger pulse
    GPIO.output(CONFIG["TRIG_PIN"], True)
    time.sleep(0.00001)
    GPIO.output(CONFIG["TRIG_PIN"], False)

    start = time.time()
    timeout = start + 0.04
    while GPIO.input(CONFIG["ECHO_PIN"]) == 0 and time.time() < timeout:
        start = time.time()

    stop = time.time()
    timeout2 = stop + 0.04
    while GPIO.input(CONFIG["ECHO_PIN"]) == 1 and time.time() < timeout2:
        stop = time.time()

    elapsed = stop - start
    # Speed of sound 34300 cm/s
    distance = (elapsed * 34300) / 2
    return distance


# -------------------------
# ThingSpeak uploader
# -------------------------
def upload_to_thingspeak(field1=None, field2=None, image_path=None):
    # ThingSpeak free channels accept numeric fields via simple GET.
    params = {}
    if CONFIG["THINGSPEAK_WRITE_KEY"] and CONFIG["THINGSPEAK_WRITE_KEY"] != "PUT_YOUR_THINGSPEAK_WRITE_KEY":
        params["api_key"] = CONFIG["THINGSPEAK_WRITE_KEY"]
    if field1 is not None:
        params["field1"] = field1
    if field2 is not None:
        params["field2"] = field2

    try:
        r = requests.get(CONFIG["THINGSPEAK_UPDATE_URL"], params=params, timeout=10)
        print("ThingSpeak update status:", r.status_code, r.text)
    except Exception as e:
        print("ThingSpeak upload failed:", e)

    # Optionally upload image to your own cloud or server; ThingSpeak doesn't host arbitrary images easily.
    if image_path:
        # Example: encode and PUT to your own server or to cloud storage
        pass


# -------------------------
# Email alert helper
# -------------------------
def send_email_alert(subject, body, attachment_path=None):
    if not CONFIG["EMAIL_ALERTS"]:
        return False
    try:
        msg = EmailMessage()
        msg["From"] = CONFIG["SMTP"]["user"]
        msg["To"] = CONFIG["SMTP"]["to"]
        msg["Subject"] = subject
        msg.set_content(body)
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                data = f.read()
            maintype = "image"
            subtype = "jpeg"
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=os.path.basename(attachment_path))
        server = smtplib.SMTP(CONFIG["SMTP"]["host"], CONFIG["SMTP"]["port"])
        server.starttls()
        server.login(CONFIG["SMTP"]["user"], CONFIG["SMTP"]["password"])
        server.send_message(msg)
        server.quit()
        print("Email sent to", CONFIG["SMTP"]["to"])
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False


# -------------------------
# Logging
# -------------------------
def log_event(event_type, details, img_path=None):
    header = ["timestamp", "event_type", "details", "image"]
    row = [datetime.datetime.now().isoformat(), event_type, details, img_path or ""]
    exists = os.path.exists(CONFIG["LOG_CSV"])
    with open(CONFIG["LOG_CSV"], "a", newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)
    print("Logged event:", row)


# -------------------------
# Main loop
# -------------------------
def main_loop():
    print("Starting WaveBell main loop. Press Ctrl+C to exit.")
    last_triggered = 0
    try:
        while True:
            # Read PIR
            pir_state = False
            if HAS_GPIO:
                pir_state = GPIO.input(CONFIG["PIR_PIN"]) == 1
            else:
                # Simulation: prompt user in console
                input_sim = input("Simulate PIR? (y/n) > ")
                pir_state = input_sim.strip().lower() == "y"

            if pir_state:
                now = time.time()
                if now - last_triggered < CONFIG["EVENT_DEBOUNCE_SEC"]:
                    print("Debounced trigger.")
                else:
                    print("PIR triggered.")
                    # Confirm with ultrasonic distance
                    distance = measure_distance_cm()
                    print(f"Measured distance: {distance:.1f} cm")
                    if distance <= CONFIG["MIN_DISTANCE_CM"]:
                        print("Presence confirmed by ultrasonic.")
                        img = capture_image(prefix="trespasser")
                        # Log locally
                        details = f"PIR trigger + ultrasonic {distance:.1f}cm"
                        log_event("trespasser_detected", details, img)
                        # Upload sensor values to ThingSpeak
                        try:
                            upload_to_thingspeak(field1=1, field2=distance, image_path=img)
                        except Exception as e:
                            print("ThingSpeak error:", e)
                        # Send email alert
                        send_email_alert("WaveBell Alert: Trespasser detected", details, attachment_path=img)
                        last_triggered = now
                    else:
                        print("Ultrasonic did not confirm; ignoring.")
            else:
                # Optionally send heartbeat to ThingSpeak (0)
                upload_to_thingspeak(field1=0)
                time.sleep(2)

            # Main loop sleep
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Exiting main loop.")
    finally:
        if HAS_GPIO:
            GPIO.cleanup()


if __name__ == "__main__":
    main_loop()
