# Muhammad Ahmad Humayoun Portfolio

A stunning neon-themed AI-powered portfolio with embedded chatbot that answers questions about Muhammad Ahmad Humayoun.

## Features

- Modern neon design with cyan/magenta theme
- 3D animated elements and particle effects
- Custom cursor with trail effect
- **AI Chatbot** - Ask questions about Muhammad Ahmad Humayoun
- Fully responsive design

## How It Works

The API key is stored in **Google Drive** and fetched at runtime by the Flask server. The key is **never stored in code** or exposed to users.

---

## Quick Start (Local Development)

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python app.py
```

### 3. Open in Browser

- **http://localhost:5000** - Main portfolio
- **http://localhost:5000/chatbot.html** - Standalone chatbot

---

## Deployment Guide

### Option 1: GitHub Pages (Chatbot Included!)

This version works on GitHub Pages! The chatbot uses client-side JavaScript to call Groq API directly.

1. Push code to GitHub
2. Go to Settings → Pages
3. Select "Deploy from a branch" → main
4. Done! Both portfolio and chatbot work!

**Note:** API key is fetched from Google Drive at runtime.

### Option 2: Railway (Better Performance)

For faster responses, deploy to Railway:

1. Go to [railway.app](https://railway.app)
2. Deploy from GitHub repo
3. Railway auto-detects Flask
4. Done!

---

## Deployment Guide

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Create new project → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python/Flask
6. Add environment variable: `PORT=80`
7. Deploy!

### Deploy to Render

1. Go to [render.com](https://render.com)
2. Create "Web Service"
3. Connect GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Deploy!

### Deploy to PythonAnywhere

1. Go to [pythonanywhere.com](https://pythonanywhere.com)
2. Open Bash console
3. `git clone your-repo`
4. `pip install -r requirements.txt`
5. Web tab → Add new app → Flask
6. Configure WSGI file to point to `app.py`

---

## Project Structure

```
├── index.html           # Main portfolio
├── chatbot.html         # Standalone chatbot page
├── app.py              # Flask server (Python)
├── requirements.txt    # Python dependencies
└── README.md
```

---

## API Key Setup

The API key is stored in Google Drive and fetched at runtime. To change the key:

1. Upload a new `key.json` file to Google Drive
2. Update the `DRIVE_KEY_URL` in `app.py`

---

## Tech Stack

- HTML5, CSS3, JavaScript (Vanilla)
- Python Flask (Backend Server)
- Groq API (AI - llama-3.1-8b-instant)

## License

MIT License
