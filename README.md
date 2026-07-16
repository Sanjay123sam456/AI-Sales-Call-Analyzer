# 🎧 AI Sales Call Analyzer

An end-to-end AI-powered Sales Call Intelligence System built for the **FitNova AI Engineer Internship Take-Home Assignment**.

The system automatically transcribes sales call recordings, performs speaker diarization, evaluates call quality using an LLM, and visualizes actionable insights through an interactive Streamlit dashboard.

---

## 🚀 Features

- Deepgram Nova-3 Speech-to-Text
- Speaker Diarization
- English, Hindi & Hinglish support
- GPT-4.1-mini evaluation via OpenRouter
- Timestamped transcript generation
- AI-generated strengths, improvements & red flags
- Radar chart visualization
- Interactive Streamlit dashboard
- Audio playback support

---

## 🛠️ Tech Stack

- Python
- Deepgram Nova-3
- OpenRouter
- GPT-4.1-mini
- Streamlit
- Plotly
- uv

---

## 📂 Dataset

A custom synthetic dataset was created specifically for this project.

- 7 realistic sales-call recordings
- Self-written and self-recorded conversations
- English, Hindi, and Hinglish calls
- Multiple customer scenarios including objections, follow-ups, and successful bookings

---

## 🔄 Workflow

```text
Audio Recording
      │
      ▼
Deepgram STT + Diarization
      │
      ▼
Transcript Parser
      │
      ▼
Timestamped Transcript
      │
      ▼
GPT-4.1-mini Evaluation
      │
      ▼
Evaluation JSON
      │
      ▼
Streamlit Dashboard
```

---

## ▶️ Run

```bash
uv sync
uv run streamlit run frontend/app.py
```

---

## 📌 Project Status

This repository contains a **working end-to-end prototype** that demonstrates the complete AI pipeline from audio transcription to dashboard visualization.

Future enhancements include SQLite/PostgreSQL integration, role-based dashboards, dashboard-based audio uploads, and real-time processing.

---

## 👨‍💻 Author

**Sanjay**

MCA (2025) | Aspiring AI / Machine Learning Engineer