import requests
import speech_recognition as sr
import RPi.GPIO as GPIO
import time
import board
import busio
from PIL import Image
from adafruit_ssd1306 import SSD1306_I2C
import os

# === CONFIG ===
TRIGGER_PHRASE = "hey clippy"
ENCODER_PIN_A = 17
ENCODER_PIN_B = 18
volume = 5  # Range: 0–10

# === OLED SETUP ===
i2c = busio.I2C(board.SCL, board.SDA)
display = SSD1306_I2C(128, 64, i2c)
display.fill(0)
display.show()

def show_clippy_face():
    image = Image.open("clippy.bmp").resize((128, 64)).convert("1")
    display.image(image)
    display.show()

def show_text(text):
    display.fill(0)
    display.text("Clippy says:", 0, 0, 1)
    display.text(text[:40], 0, 16, 1)
    display.show()

# === ROTARY ENCODER SETUP ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(ENCODER_PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENCODER_PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def update_volume(channel):
    global volume
    if GPIO.input(ENCODER_PIN_B):
        volume = min(volume + 1, 10)
    else:
        volume = max(volume - 1, 0)
    print(f"Volume: {volume}")

GPIO.add_event_detect(ENCODER_PIN_A, GPIO.FALLING, callback=update_volume)

# === VOICE LISTENER ===
def listen_for_trigger():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for trigger...")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            print("Heard:", text)
            return TRIGGER_PHRASE in text.lower()
        except:
            return False

def get_user_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for user input...")
        audio = r.listen(source)
        return r.recognize_google(audio)

def get_clippy_response(prompt):
    url = "https://ai.hackclub.com/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

def speak(text):
    os.system(f'espeak -a {volume * 10} "{text}"')

# === MAIN LOOP ===
show_clippy_face()

while True:
    if listen_for_trigger():
        try:
            user_input = get_user_input()
            reply = get_clippy_response(user_input)
            show_text(reply)
            speak(reply)
        except Exception as e:
            print("Error:", e)
