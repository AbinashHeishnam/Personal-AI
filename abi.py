# =======================
# Personal AI Assistant
# VS Code Version with Voice Input/Output
# =======================

# Step 1: Install dependencies (run in terminal once)
# pip install torch transformers bitsandbytes accelerate sentence-transformers wikipedia requests googletrans==4.0.0-rc1 vosk sounddevice pywin32 langdetect

# -----------------------
# Imports
# -----------------------
import time
import json
import queue
import requests
import wikipedia
import torch
from langdetect import detect
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from googletrans import Translator
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import win32com.client

# -----------------------
# TTS Setup (Windows)
# -----------------------
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Rate = 0
speaker.Volume = 100

def speak(text):
    speaker.Speak(text)

# -----------------------
# Speech-to-Text Setup (Vosk)
# -----------------------
q = queue.Queue()
model_stt = Model("vosk-model-small-en-us-0.15")  # put your Vosk model folder here
rec = KaldiRecognizer(model_stt, 16000)

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen():
    """Capture user voice and return recognized text"""
    print("🎤 Listening...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    print("🗣️ You said:", text)
                    return text

# -----------------------
# Translator
# -----------------------
translator = Translator()

def detect_language(text):
    try:
        return translator.detect(text).lang
    except:
        return "en"

def translate_text(text, target_lang="en"):
    try:
        return translator.translate(text, dest=target_lang).text
    except:
        return text

# -----------------------
# Load AI Model (Mistral-7B)
# -----------------------
model_name = "mistralai/Mistral-7B-Instruct-v0.2"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)
model.eval()
print("✅ Mistral 7B Instruct loaded successfully!")

# -----------------------
# News API Setup
# -----------------------
NEWS_API_KEY = "a58eb0d36c1f411b95902c1533c1e04c"

def get_current_affairs(query):
    try:
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
        data = requests.get(url, timeout=5).json()
        if data.get("status") != "ok" or not data.get("articles"):
            return None
        news = [f"- {a['title']} ({a['source']['name']})" for a in data["articles"]]
        return "Latest news:\n" + "\n".join(news)
    except:
        return None

def get_wiki_context(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        return f"Wikipedia info:\n{summary}"
    except:
        return "No Wikipedia info found."

# -----------------------
# Personal Assistant Behavior
# -----------------------
def assistant_behavior(user_input):
    text = user_input.lower()
    if "i am feeling" in text or "i feel" in text:
        return "I'm here for you. Want to talk about what's bothering you?"
    if "help me" in text or "can you help" in text:
        return "Of course. Tell me exactly what you need help with."
    if "thank" in text:
        return "You're welcome 🙂"
    return None

# -----------------------
# Generate AI Answer
# -----------------------
def generate_answer(user_input):
    # 1️⃣ Personal assistant response
    personal = assistant_behavior(user_input)
    if personal:
        return personal

    # 2️⃣ Current affairs or Wikipedia
    news = get_current_affairs(user_input)
    context = news if news else get_wiki_context(user_input)

    # 3️⃣ Build prompt
    prompt = f"""
You are a helpful personal AI assistant.
Answer concisely and ONLY the current question.

Context:
{context}

Question: {user_input}
Answer:
"""

    # 4️⃣ Tokenize input
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=2048
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # 5️⃣ Generate output
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.3,
            top_p=0.9,
            repetition_penalty=1.2,
            eos_token_id=tokenizer.eos_token_id
        )

    # 6️⃣ Decode output
    return tokenizer.decode(output[0], skip_special_tokens=True).split("Answer:")[-1].strip()

# -----------------------
# Main Loop
# -----------------------
TARGET_LANG = "en"  # keep English output

print("🧠 Personal AI Assistant (say 'exit' to quit)\n")

while True:
    user_text = listen()  # <-- voice input
    if user_text.lower() in ["exit", "quit"]:
        speak("Goodbye! 👋")
        break

    # Detect language
    user_lang = detect_language(user_text)

    # Translate input if needed
    input_for_ai = translate_text(user_text, target_lang="en") if user_lang != "en" else user_text

    print("⏳ Thinking...")
    ai_response = generate_answer(input_for_ai)

    # Translate AI response if needed
    translated_response = translate_text(ai_response, target_lang=TARGET_LANG)

    # Output response
    print("\nAssistant:", translated_response, "\n")
    speak(translated_response)
    print("-" * 50)
