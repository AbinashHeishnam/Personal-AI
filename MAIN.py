import subprocess
import sounddevice as sd
import queue
import json
import win32com.client
import time
import requests
from textblob import TextBlob
from vosk import Model, KaldiRecognizer
import re
import yfinance as yf

# ================= CONFIG =================
OLLAMA_PATH = r"C:\Users\ABINASH HEISHNAM\AppData\Local\Programs\Ollama\ollama.exe"
MODEL_NAME = "mistral"
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"  # Replace with your key

# ================= GLOBAL STATE ==========
IS_SPEAKING = False
conversation_history = []  # last 20 messages for context
last_entities = {}  # remember last mentioned topics for pronouns
mode = "voice"  # default mode: voice, can switch to text

# ================= TTS ===================
speaker = win32com.client.Dispatch("SAPI.SpVoice")
for voice in speaker.GetVoices():
    if "female" in voice.GetDescription().lower() or "zira" in voice.GetDescription().lower():
        speaker.Voice = voice
        break
speaker.Rate = 0
speaker.Volume = 100

def speak(text):
    global IS_SPEAKING
    IS_SPEAKING = True
    print("AI:", text)
    speaker.Speak(text)
    time.sleep(0.3)
    IS_SPEAKING = False

# ================= STT ===================
model = Model("vosk-model-small-en-us-0.15")
rec = KaldiRecognizer(model, 16000)
audio_q = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if IS_SPEAKING:
        return
    audio_q.put(bytes(indata))

# ================= EMOTIONAL LAYER =================
def emotional_layer(text):
    conversation_history.append(text)
    sentiment = TextBlob(text).sentiment.polarity
    if sentiment < -0.2:
        return "Hey, I sense you might be feeling a bit down . I’m here for you, tell me more!"
    elif sentiment > 0.5:
        return "Yay! That’s awesome . I’m really happy for you!"
    return None

# ================= QUERY DETECTION =================
def is_fact_query(text):
    text_lower = text.lower()
    fact_keywords = ["weather", "stock", "price", "news", "current", "today", "latest", "temperature", "update", "updates", "forecast", "who", "what", "when", "where"]
    return any(word in text_lower for word in fact_keywords)

def is_chitchat(text):
    chit_keywords = ["hello", "hi", "how are you", "tell me a joke", "bye", "thanks"]
    text_lower = text.lower()
    if is_fact_query(text_lower):
        return False
    return any(word in text_lower for word in chit_keywords)

def is_nonsense(text):
    nonsense_words = ["asdf", "qwerty", "flibber", "floob", "xyz"]
    return any(word in text.lower() for word in nonsense_words)

def needs_clarification(text):
    confusing_words = ["not raining or raining", "but not", "either or", "what thing", "which one"]
    return any(word in text.lower() for word in confusing_words)

# ================= LIVE INFORMATION =================
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        r = requests.get(url).json()
        desc = r["weather"][0]["description"]
        temp = r["main"]["temp"]
        humidity = r["main"]["humidity"]
        wind = r["wind"]["speed"]
        return f"{city.title()} right now: {desc}, {temp}°C 🌡️, Humidity {humidity}%, Wind {wind} m/s."
    except Exception:
        return f"Oops! I couldn't fetch live weather for {city}. Try again in a bit."

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"][-1]
        change = stock.history(period="1d")["Close"][-1] - stock.history(period="2d")["Close"][-2]
        arrow = "🔺" if change >= 0 else "🔻"
        return f"{ticker.upper()} is at {price:.2f} {arrow} ({change:.2f})"
    except Exception:
        return f"Couldn't fetch live stock info for {ticker}"

def get_live_info(query):
    text_lower = query.lower()
    # Weather
    if "weather" in text_lower:
        match = re.search(r"weather in ([a-zA-Z ]+)", text_lower)
        city = match.group(1).strip() if match else "your city"
        return get_weather(city)
    # Stocks
    tickers = ["AAPL", "TSLA", "AMZN", "GOOGL"]
    for t in tickers:
        if t.lower() in text_lower:
            return get_stock_price(t)
    # DuckDuckGo fallback for general knowledge
    try:
        response = requests.get("https://api.duckduckgo.com/", params={"q": query, "format": "json"})
        data = response.json()
        abstract = data.get("AbstractText")
        if abstract:
            return abstract
        # if no abstract, maybe try related topics
        related = data.get("RelatedTopics")
        if related and len(related) > 0:
            return related[0].get("Text", "I found something related but can't display it properly.")
        return None
    except Exception:
        return None

# ================= MULTI-PART / INTENT =================
def split_multi_part_query(text):
    parts = re.split(r'\band\b|,|;|then|also', text.lower())
    return [p.strip() for p in parts if p.strip()]

def extract_intent(text):
    filler_words = ["some", "dumb", "please", "like", "tom"]
    words = text.split()
    keywords = [w for w in words if w not in filler_words]
    return " ".join(keywords)

# ================= OLLAMA LOGIC =================
def ask_ollama(user_text):
    emotion_reply = emotional_layer(user_text)
    if emotion_reply:
        return emotion_reply

    if needs_clarification(user_text):
        return "Hmm… I’m a bit confused by that question. Can you rephrase it?"

    if is_nonsense(user_text):
        return "Haha , that sounds fun but I’m not sure that’s real."

    sub_queries = split_multi_part_query(user_text)
    responses = []

    for sub_query in sub_queries:
        clean_query = extract_intent(sub_query)

        # --- FACT QUERY FIRST (priority over chit-chat)
        live_info = get_live_info(clean_query)
        if live_info:
            responses.append(live_info)
            continue

        # --- Chit-chat fallback
        if is_chitchat(clean_query):
            responses.append("Hey! I'm AI, your friendly assistant. What’s up?")
            continue

        # --- Ollama fallback
        wants_detail = any(phrase in clean_query for phrase in ["explain", "how does", "full explanation", "deep explanation", "why"])
        system_prompt = """
You are Jarvis, an ultra-human personal assistant. Speak casually, like a friend.
Use small jokes, emojis, and human-like phrases.
Answer naturally and friendly.
""" if wants_detail else """
You are Jarvis, an ultra-human personal assistant. Keep it casual, short, friendly, like a real human.
"""

        history_context = "\n".join(conversation_history[-20:])
        full_prompt = f"{system_prompt}\nConversation history:\n{history_context}\nUser: {clean_query}\nJarvis:"

        try:
            process = subprocess.Popen([OLLAMA_PATH, "run", MODEL_NAME],
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(full_prompt.encode("utf-8"), timeout=120)
            reply = stdout.decode("utf-8", errors="ignore").strip()
            conversation_history.append(f"Jarvis: {reply}")
            if len(conversation_history) > 40:
                conversation_history[:20] = []
            responses.append(reply)
        except Exception:
            responses.append("Oops! Something went wrong. Can you ask again?")

    return "\n".join(responses)

# ================= MAIN LOOP =================
print("AI is online (Human-like, Multi-part, Live Info, Text + Voice)")
speak("Hey Abinash! AI is online . Ready when you are.")
print("Say 'exit' or 'quit' to stop\n")
print("Type your query anytime or speak! (type 'voice' to switch to speaking)")

with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=audio_callback):
    while True:
        if mode == "voice":
            print(" Listening... Speak now")
            text = ""
            while True:
                data = audio_q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    break
        else:  # text mode
            text = input("Type your query (or 'voice' to switch to speech): ").strip()
            if text.lower() == "voice":
                mode = "voice"
                continue

        if not text:
            continue

        print(" You:", text)

        if any(word in text.lower() for word in ["exit", "quit", "stop"]):
            speak("Bye Abinash! I’ll be here whenever you need me .")
            break

        reply = ask_ollama(text)
        speak(reply)

        # Ask if user wants to switch input mode
        if mode == "voice":
            user_choice = input("\n(Type 'text' to type instead of speaking, or press Enter to continue voice): ").strip().lower()
            if user_choice == "text":
                mode = "text"
