# 🚀 Muhammad Ahmad Humayoun Portfolio - Complete Setup Guide

> A stunning AI-powered portfolio with JOGI chatbot. This guide will walk you through setting up your own copy.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Prerequisites](#-prerequisites)
3. [Files & Structure](#-files--structure)
4. [API Key Setup](#-api-key-setup)
5. [Local Development](#-local-development)
6. [Deploy to Replit](#-deploy-to-replit)
7. [Deploy to Railway](#-deploy-to-railway)
8. [Deploy to Render](#-deploy-to-render)
9. [Deploy to GitHub Pages](#-deploy-to-github-pages)
10. [Customization](#-customization)
11. [Troubleshooting](#-troubleshooting)

---

## 📊 Project Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PORTFOLIO ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐     ┌──────────┐     ┌──────────────────┐   │
│   │  User    │────▶│ Browser  │────▶│    Flask Server   │   │
│   │ (Visitor)│     │          │     │    (Backend)     │   │
│   └──────────┘     └──────────┘     └────────┬─────────┘   │
│                                               │            │
│                   ┌───────────────────────────┼────────┐   │
│                   │                           │            │            │
│                   ▼                           ▼            ▼            │
│            ┌──────────────┐      ┌──────────────┐  ┌─────────────┐  │
│            │  index.html │      │ chatbot.html │  │   AI Chat   │  │
│            │ (Portfolio) │      │ (JOGI Chat) │  │   (Groq)   │  │
│            └──────────────┘      └──────────────┘  └─────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Features:

- 🌟 Modern neon/cyberpunk design with cyan & magenta
- 🤖 **JOGI AI** - Smart chatbot answering questions about Ahmad
- 🎵 Background music player
- 🎤 Voice command navigation
- 📱 Fully responsive
- 💫 Animated 3D floating elements
- 📅 Meeting booking system

---

## ✅ Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.9+ | Backend server |
| Git | Any | Version control |
| Code Editor | VS Code Recommended | Editing code |

### Install Python:
```
# Download from: https://www.python.org/downloads/
# IMPORTANT: Check "Add Python to PATH"
```

---

## 📁 Files & Structure

```
📦 AI-Portfolio/
│
├── 🌐 HTML Files (Frontend)
│   ├── index.html          ← Main portfolio page
│   ├── chatbot.html       ← JOGI AI chatbot
│   ├── book.html         ← Meeting booking
│   └── jogiworld.html    ← 3D experience
│
├── ⚙️ Backend (Python)
│   ├── app.py            ← Flask server
│   └── requirements.txt  ← Python packages
│
├── 📄 Configuration
│   ├── Procfile          ← For deployment
│   ├── .replit          ← Replit config
│   └── replit.md       ← Replit instructions
│
├── 📊 Data
│   ├── meetings.csv      ← Booked meetings
│   └── contacts.csv    ← Contact submissions
│
├── 🖼️ Assets
│   ├── profilepictureAhmad.jpeg
│   ├── favicon.svg
│   ├── favicon.ico
│   └── bgMusic1.mp3
│
└── 📝 Documentation
    ├── README.md
    └── SETUP.md          ← YOU ARE HERE
```

---

## 🔑 API Key Setup

> This portfolio uses Groq AI for the JOGI chatbot. You need your own API key.

### Option 1: Get a Free Groq API Key

```
┌─────────────────────────────────────────────────────────┐
│                 GET GROQ API KEY                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Go to: https://console.groq.com              │
│                                                         │
│  2. Sign up / Login                                     │
│                                                         │
│  3. Navigate to: API Keys                           │
│                                                         │
│  4. Click "Create API Key"                          │
│                                                         │
│  5. Copy your key (starts with gsk_...)           │
│                                                         │
│  ⚠️ FREE: 60,000 tokens/minute!                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Option 2: Set Up Google Drive (For Production)

This portfolio fetches the API key from Google Drive for security:

```
┌─────────────────────────────────────────────────────────┐
│           GOOGLE DRIVE KEY STORAGE                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Create a Google Sheet or Google Doc                │
│                                                         │
│  2. Add your API key as text                         │
│                                                         │
│  3. Make it "Anyone with link can view"              │
│                                                         │
│  4. Copy the sharing URL                          │
│                                                         │
│  5. In app.py, update DRIVE_KEY_URL:               │
│     DRIVE_KEY_URL = "your-google-drive-url"        │
│                                                         │
│  ⚠️ This keeps key out of public code!           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### OR直接 in app.py (Simple):

```python
# In app.py, find this line:
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Replace with your key (NOT recommended for public repos):
GROQ_API_KEY = "gsk_your_key_here"
```

---

## 💻 Local Development

### Step 1: Clone the Repository

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/AI-Portfolio.git

# Enter directory
cd AI-Portfolio
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 3: Set Up API Key

```bash
# Set API key as environment variable
export GROQ_API_KEY="gsk_your_key_here"

# On Windows (Command Prompt):
set GROQ_API_KEY=gsk_your_key_here

# On Windows (PowerShell):
$env:GROQ_API_KEY="gsk_your_key_here"
```

### Step 4: Run the Server

```bash
python app.py
```

### Step 5: Open in Browser

```
┌────────────────────────────────────────┐
│           LOCAL URLs                    │
├────────────────────────────────────────┤
│                                        │
│  🌐 http://localhost:5000              │
│      ↓ Main portfolio                  │
│                                        │
│  💬 http://localhost:5000/chatbot.html │
│      ↓ JOGI chatbot                  │
│                                        │
│  📅 http://localhost:5000/book.html  │
│      ↓ Meeting booking              │
│                                        │
└────────────────────────────────────────┘
```

---

## ☁️ Deploy to Replit

> Easiest deployment - fully free tier!

### Step-by-Step:

```
┌─────────────────────────────────────────────────────────────┐
│                 DEPLOY TO REPLIT                        │
├─────────────────────────────────────────────────────────────┤
│                                                      │
│  1. Go to https://replit.com                          │
│                                                      │
│  2. Click "+ Create Replit"                          │
│                                                      │
│  3. Select "Import from GitHub"                     │
│                                                      │
│  4. Choose your repository                        │
│                                                      │
│  5. Set Environment Variable:                    │
│     ─────────────────────────────────           │
│     Key: GROQ_API_KEY                            │
│     Value: gsk_your_api_key_here                  │
│     ─────────────────────────────────           │
│                                                      │
│  6. Click "Run" (Green button)                   │
│                                                      │
│  7. Get your URL from the preview                 │
│                                                      │
└─────────────────────────────────────────────────────────────┘
```

### Replit Configuration (.replit):

```toml
modules = ["python-3.10"]
run = "python app.py"
hidden = [".github", ".git", "venv", "__pycache__"]

[env]
GROQ_API_KEY = ""

[nix]
channel = "stable"
```

---

## 🚂 Deploy to Railway

> Best for production - free $5 credit/month!

### Steps:

```
┌─────────────────────────────────────────────────────────────┐
│               DEPLOY TO RAILWAY                           │
├─────────────────────────────────────────────────────────────┤
│                                                      │
│  1. Go to https://railway.app                        │
│                                                      │
│  2. Sign up with GitHub                           │
│                                                      │
│  3. Click "+ New Project"                        │
│                                                      │
│  4. Select "Deploy from GitHub repo"           │
│                                                      │
│  5. Choose your repository                     │
│                                                      │
│  6. Add Environment Variable:                 │
│     ──────────────────────────────────────     │
│     GROQ_API_KEY = gsk_your_api_key            │
│     ──────────────────────────────────────     ��
│                                                      │
│  7. Deploy! 🎉                                │
│                                                      │
│  8. Your URL: https://your-app.railway.app     │
│                                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Deploy to Render

> Free web service available!

### Steps:

```
┌─────────────────────────────────────────────────────────────┐
│                DEPLOY TO RENDER                           │
├─────────────────────────────────────────────────────────────┤
│                                                      │
│  1. Go to https://render.com                          │
│                                                      │
│  2. Create "Web Service"                         │
│                                                      │
│  3. Connect GitHub repo                         │
│                                                      │
│  4. Configure:                                 │
│     ──────────────────────────────────────              │
│     Name: your-portfolio                        │
│     Branch: main                            │
│     Build Command: pip install -r requirements.txt │
│     Start Command: gunicorn app:app        │
│     ──────────────────────────────────────              │
│                                                      │
│  5. Add Environment Variable:              │
│     ──────────────────────────────────────             │
│     GROQ_API_KEY = gsk_your_api_key     │
│     ──────────────────────────────────────             │
│                                                      │
│  6. Deploy! 🎉                               │
│                                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📄 Deploy to GitHub Pages

> Easy but no backend (static only - no chatbot!)

### Steps:

```
┌─────────────────────────────────────────────────────────────┐
│            DEPLOY TO GITHUB PAGES                        │
├─────────────────────────────────────────────────────────────┤
│                                                      │
│  1. Go to your GitHub repo                        │
│                                                      │
│  2. Settings → Pages                            │
│                                                      │
│  3. Source: "Deploy from branch"              │
│                                                      │
│  4. Branch: "main"                      │
│                                                      │
│  5. Folder: "/" (root)                    │
│                                                      │
│  6. Save                                        │
│                                                      │
│  7. Your URL: https://username.github.io/ repo │
│                                                      │
│  ⚠️ NOTE: No Python backend = no chatbot!    │
│     JOGI AI won't work on GitHub Pages      │
│                                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎀 Customization

### 1. Change Name & Info

In `index.html`:

```html
<!-- Find and edit these: -->
<span class="name">Muhammad Ahmad</span>
<span class="surname">Humayoun</span>
<div class="hero-badge">Co-Founder of Xynova</div>
```

### 2. Change Profile Picture

Replace `profilepictureAhmad.jpeg` with your photo (keep same filename or update HTML).

### 3. Change Colors

In `index.html`, find CSS variables:

```css
:root { 
    --primary: #00f0ff;      /* Cyan - change to your color */
    --secondary: #ff00ff;     /* Magenta */
    --tertiary: #00ff88;      /* Green */
}
```

### 4. Update Chatbot Knowledge

In `app.py`, edit the `SYSTEM_PROMPT`:

```python
SYSTEM_PROMPT = """You are JOGI, AI assistant for...
Update your info here about yourself..."""
```

### 5. Change Social Links

In `index.html`, find and update:

```html
<a href="https://linkedin.com/in/yourprofile">LinkedIn</a>
<a href="https://github.com/yourusername">GitHub</a>
<a href="https://twitter.com/yourhandle">Twitter</a>
```

---

## 🔧 Troubleshooting

### Common Issues:

| Problem | Solution |
|--------|----------|
| **Port 5000 in use** | `python app.py` or change port |
| **API key error** | Check GROQ_API_KEY is set |
| **Page not loading** | Check Flask is running |
| **Chatbot not responding** | Check API key + internet |
| **Music not playing** | Check bgMusic1.mp3 exists |

### Get Help:

```
┌─────────────────────────────────────────────┐
│           NEED HELP?                        │
├─────────────────────────────────────────────┤
│                                     │
│  📧 Email: ahmad@xynova.ai            │
│                                     │
│  💬 Issues: Open GitHub issue       │
│                                     │
│  📱 Check app.py logs for errors   │
│                                     │
└─────────────────────────────────────────────┘
```

---

## 📄 License

MIT License - Use this for your own portfolio!

---

## 🙏 Credits

- **Design**: Muhammad Ahmad Humayoun
- **AI**: Groq (llama-3.1-8b-instant)
- **Inspiration**: Neon/cyberpunk aesthetic

---

> Made with ❤️ by Ahmad | © 2024