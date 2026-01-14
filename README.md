# 🤖 Personal AI Assistant (Jarvis-Style)

A human-like **Personal AI Assistant** built using Python that supports **voice and text interaction**, **emotional intelligence**, **live information**, and **local AI inference** using **Ollama**.

This assistant behaves like a real companion — casual, friendly, emotionally aware, and capable of answering both general and real-time queries.

---

## 🚀 Features

### 🎙️ Voice + Text Interaction
- Offline **Speech-to-Text** using Vosk
- Natural **Text-to-Speech** using Windows SAPI
- Seamless switching between voice and text modes

### 🧠 Emotional Intelligence
- Sentiment analysis using TextBlob
- Empathetic responses when the user sounds sad or excited
- Human-like conversational behavior

### 🌐 Live Information
- 🌦️ Real-time weather updates (OpenWeather API)
- 📈 Live stock prices (Yahoo Finance)
- 🔎 General knowledge (DuckDuckGo API)

### 🔍 Smart Query Handling
- Supports multi-part queries  
  Example: *“Tell me the weather in Delhi and Tesla stock price”*
- Detects:
  - Fact-based questions
  - Chit-chat
  - Nonsense input
  - Ambiguous queries (asks for clarification)

### 🤖 Local AI (Privacy Friendly)
- Uses **Ollama** for local LLM inference
- Default model: **mistral**
- No cloud dependency for AI responses

---

## 🛠️ Tech Stack

- Python
- Ollama (Local LLM)
- Vosk (Speech Recognition)
- SoundDevice (Audio Input)
- Windows SAPI (Text-to-Speech)
- TextBlob (Sentiment Analysis)
- OpenWeather API
- Yahoo Finance (yfinance)
- DuckDuckGo API

---

## 📂 Project Structure

personal_ai/
│
├── main.py # Main AI assistant script
├── vosk-model/ # Offline speech recognition model
├── README.md # Project documentation
├── requirements.txt # Python dependencies
└── venv/ # Virtual environment


---

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/AbinashHeishnam/Personal-AI.git
cd Personal-AI


The assistant will:

Greet you via voice

Start listening immediately

Respond using voice and text

###🗣️ Example Commands

“What’s the weather in Mumbai?”

“Tell me Tesla stock price”

“Explain how AI works”

“I’m feeling sad today”

“Switch to text mode”

“Exit”

##🔐 Privacy & Ethics

Runs completely locally

No voice or data is uploaded externally

Built for educational and personal use only

##📌 Future Enhancements

Multilingual speech support

PC automation (open apps, control system)

Long-term memory

GUI interface (ChatGPT-style)

Wake-word detection (“Hey Jarvis”)

##👨‍💻 Author

Abinash Heishnam
B.Tech Computer Science Engineer | AI & Cybersecurity Enthusiast

🔗 GitHub: https://github.com/AbinashHeishnam