# Muhammad Ahmad Humayoun Portfolio

## Overview
A neon-themed AI-powered portfolio website with an embedded AI chatbot (JOGI) that answers questions about Muhammad Ahmad Humayoun.

## Architecture
- **Backend**: Python Flask server (`app.py`) serving both static files and API
- **Frontend**: Vanilla HTML/CSS/JS (`index.html`, `chatbot.html`)
- **AI**: Groq API (llama-3.1-8b-instant model) via Flask backend
- **API Key**: Fetched at runtime from Google Drive (never stored in code)

## Project Structure
```
├── app.py           # Flask server - serves static files + /api/chat endpoint
├── index.html       # Main portfolio page
├── chatbot.html     # JOGI chatbot page
├── requirements.txt # Python dependencies (Flask, requests)
├── Procfile         # Process definition
└── README.md
```

## Running the App
- **Workflow**: "Start application" runs `python app.py` on port 5000
- **Dev server**: Flask on `0.0.0.0:5000`
- **Production**: Gunicorn via `gunicorn --bind=0.0.0.0:5000 --reuse-port app:app`

## Key Features
- Neon cyan/magenta design with 3D animated elements
- Custom cursor with trail effect
- Particle effects
- JOGI AI Chatbot (Groq API / llama-3.1-8b-instant)
- Routes: `/` → index.html, `/chatbot.html` → chatbot, `/api/chat` → AI endpoint

## Dependencies
- Flask==3.0.0
- requests==2.31.0
- gunicorn (for production)
