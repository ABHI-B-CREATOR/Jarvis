import speech_recognition as sr
import os
import subprocess
import time
import logging
import random
from gtts import gTTS
import playsound
import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(filename='jarvis.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Text-to-Speech function
def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save("temp.mp3")
    playsound.playsound("temp.mp3")
    os.remove("temp.mp3")
    logging.info(f"Spoken: {text}")

# Initialize speech recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 3000
recognizer.dynamic_energy_threshold = True

# Conversational responses
RESPONSES = {
    "welcome": ["JARVIS online, ready to assist!", "Hello, I’m here to help!", "JARVIS activated!"],
    "error": ["Sorry, I faced an issue. Try again?", "Oops, something went wrong.", "Trouble here, repeat please?"],
    "success": ["Done!", "Task completed!", "All set!"],
    "unknown": ["I didn’t get that. Try 'open app'?", "Unsure, give me a clear command.", "Could you repeat?"]
}

# Battery monitoring thread
def monitor_battery():
    while True:
        try:
            output = subprocess.check_output("dumpsys battery", shell=True).decode()
            level = int(re.search(r"level: (\d+)", output).group(1))
            if level <= 20 and not hasattr(monitor_battery, "alerted"):
                speak(f"Warning: Battery level is {level}%. Please charge soon.")
                monitor_battery.alerted = True
            elif level > 20:
                if hasattr(monitor_battery, "alerted"):
                    del monitor_battery.alerted
        except Exception as e:
            logging.error(f"Battery monitor error: {e}")
        time.sleep(300)  # Check every 5 minutes

# Listen function
def listen():
    try:
        with sr.Microphone() as source:
            print("Listening...")  # Use print for Termux console feedback
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
            command = recognizer.recognize_google(audio).lower().strip()
            logging.info(f"Heard command: {command}")
            return command
    except sr.WaitTimeoutError:
        speak(random.choice(RESPONSES["error"]))
        return None
    except sr.UnknownValueError:
        speak(random.choice(RESPONSES["error"]))
        return None
    except sr.RequestError as e:
        speak("No internet for speech. Check connection.")
        logging.error(f"Request error: {e}")
        return None
    except Exception as e:
        speak("Microphone issue. Check permissions.")
        logging.error(f"Listen error: {e}")
        return None

# Process commands
def process_command(command):
    phone_apps = {
        "whatsapp": "am start -n com.whatsapp/.Main",
        "messages": "am start -n com.google.android.apps.messaging/.ui.ConversationListActivity",
        "phone": "am start -a android.intent.action.DIAL",
        "camera": "am start -n com.google.android.GoogleCamera/com.android.camera.CameraActivity",
        "browser": "am start -a android.intent.action.VIEW -d https://www.google.com"
    }

    if command.startswith("open "):
        app_name = command.replace("open ", "").strip()
        speak(f"Opening {app_name}...")
        try:
            if app_name.lower() in phone_apps:
                os.system(phone_apps[app_name.lower()])
                speak(random.choice(RESPONSES["success"]))
            else:
                speak(f"App {app_name} not found.")
        except Exception as e:
            speak(f"Failed to open {app_name}.")
            logging.error(f"Open error: {e}")

    elif command.startswith("close "):
        app_name = command.replace("close ", "").strip()
        speak(f"Closing {app_name}...")
        try:
            if app_name.lower() in phone_apps:
                os.system(f"am force-stop {app_name.lower().split('.')[1]}")
                speak(random.choice(RESPONSES["success"]))
            else:
                speak(f"App {app_name} not recognized.")
        except Exception as e:
            speak(f"Failed to close {app_name}.")
            logging.error(f"Close error: {e}")

    elif command.startswith("type "):
        text = command.replace("type ", "").strip()
        speak(f"Typing {text}...")
        try:
            os.system(f"input text '{text}'")
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Typing failed.")
            logging.error(f"Type error: {e}")

    elif command.startswith("search ") and " for " in command:
        parts = command.split(" for ")
        if len(parts) == 2:
            _, query = parts
            speak(f"Searching for {query}...")
            try:
                os.system(f"am start -a android.intent.action.WEB_SEARCH -d https://www.google.com/search?q={query.replace(' ', '+')}")
                speak(random.choice(RESPONSES["success"]))
            except Exception as e:
                speak("Search failed.")
                logging.error(f"Search error: {e}")
        else:
            speak(random.choice(RESPONSES["unknown"]))

    elif command == "click photo":
        speak("Taking a photo...")
        try:
            os.system("am start -n com.google.android.GoogleCamera/com.android.camera.CameraActivity")
            time.sleep(2)  # Allow camera to open
            os.system("input keyevent 27")  # Capture photo
            time.sleep(1)
            os.system("am force-stop com.google.android.GoogleCamera")
            speak("Photo clicked!")
        except Exception as e:
            speak("Photo capture failed.")
            logging.error(f"Photo error: {e}")

    elif command == "record video":
        speak("Starting video recording...")
        try:
            os.system("am start -n com.google.android.GoogleCamera/com.android.camera.CameraActivity")
            time.sleep(2)
            os.system("input keyevent 27")  # Switch to video (may vary by device)
            os.system("input keyevent 27")  # Start recording
            time.sleep(5)  # Record for 5 seconds
            os.system("input keyevent 27")  # Stop recording
            time.sleep(1)
            os.system("am force-stop com.google.android.GoogleCamera")
            speak("Video recorded!")
        except Exception as e:
            speak("Video recording failed.")
            logging.error(f"Video error: {e}")

    elif "volume up" in command:
        speak("Raising volume...")
        try:
            for _ in range(5):
                os.system("input keyevent 24")
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Volume up failed.")
            logging.error(f"Volume up error: {e}")

    elif "volume down" in command:
        speak("Lowering volume...")
        try:
            for _ in range(5):
                os.system("input keyevent 25")
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Volume down failed.")
            logging.error(f"Volume down error: {e}")

    elif "brightness up" in command:
        speak("Increasing brightness...")
        try:
            os.system("settings put system screen_brightness 200")
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Brightness up failed.")
            logging.error(f"Brightness up error: {e}")

    elif "brightness down" in command:
        speak("Decreasing brightness...")
        try:
            os.system("settings put system screen_brightness 50")
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Brightness down failed.")
            logging.error(f"Brightness down error: {e}")

    elif "toggle wifi" in command:
        speak("Toggling Wi-Fi...")
        try:
            os.system("svc wifi enable")
            time.sleep(1)
            os.system("svc wifi disable")
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Wi-Fi toggle failed.")
            logging.error(f"Wi-Fi error: {e}")

    elif "toggle mobile data" in command:
        speak("Toggling mobile data...")
        try:
            os.system("svc data enable")
            time.sleep(1)
            os.system("svc data disable")
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Mobile data toggle failed.")
            logging.error(f"Mobile data error: {e}")

    elif "toggle hotspot" in command:
        speak("Toggling hotspot...")
        try:
            os.system("am start -n com.android.settings/.wifi.tether.WifiTetherSettings")
            time.sleep(2)
            os.system("input tap 500 1000")  # Approximate tap (adjust coordinates)
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Hotspot toggle failed.")
            logging.error(f"Hotspot error: {e}")

    elif "toggle aeroplane mode" in command:
        speak("Toggling aeroplane mode...")
        try:
            os.system("settings put global airplane_mode_on 1")
            os.system("am broadcast -a android.intent.action.AIRPLANE_MODE")
            time.sleep(1)
            os.system("settings put global airplane_mode_on 0")
            os.system("am broadcast -a android.intent.action.AIRPLANE_MODE")
            speak(random.choice(RESPONSES["success"]))
        except Exception as e:
            speak("Aeroplane mode toggle failed.")
            logging.error(f"Aeroplane mode error: {e}")

    elif "read text" in command:
        speak("Simulating text reading. You have a message: 'Hi, meet at 5 PM.'")
        speak("Real SMS needs permission setup.")

    else:
        speak(random.choice(RESPONSES["unknown"]))

# Main function
def main():
    threading.Thread(target=monitor_battery, daemon=True).start()
    speak(random.choice(RESPONSES["welcome"]))
    while True:
        command = listen()
        if command:
            process_command(command)

if __name__ == "__main__":
    main()