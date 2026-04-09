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
7. [Customization](#-customization)
8. [Troubleshooting](#-troubleshooting)

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
│            │  index.html │      │ chatbot.html  │  │   AI Chat   │  │
│            │ (Portfolio) │      │ (JOGI Chat)   │  │   (Groq)   │  │
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
│   ├── .replit          ← Replit config
│   └── replit.md       ← Replit instructions
│
└── 📝 Documentation
    ├── README.md
    └── SETUP.md          ← YOU ARE HERE
```

---

## 🔑 API Key Setup

> This portfolio uses **Groq AI** for the JOGI chatbot. You need your own API key.
> 
> **IMPORTANT**: The API key is stored in environment variables - NEVER in the code!

### Get a Free Groq API Key

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

### Environment Variables

```
┌─────────────────────────────────────────────────────────────────┐
│              ENVIRONMENT VARIABLES GUIDE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📌 GROQ_API_KEY (REQUIRED for Chatbot)                        │
│  ─────────────────────────────────────                          │
│  Purpose: Powers the JOGI AI chatbot                           │
│  Get from: https://console.groq.com                            │
│                                                                  │
│  📌 DATABASE_URL (Auto-created by Replit)                      │
│  ─────────────────────────────────────────                      │
│  Purpose: Stores meeting bookings and contact form messages   │
│  Get from: Add PostgreSQL via Replit's Database tool           │
│                                                                  │
│  📌 TELEGRAM_BOT_TOKEN (OPTIONAL)                              │
│  ─────────────────────────────────────                          │
│  Purpose: Sends contact form submissions to Telegram          │
│  Get from: @BotFather on Telegram                               │
│                                                                  │
│  📌 TELEGRAM_CHAT_ID (OPTIONAL)                                │
│  ─────────────────────────────────────                          │
│  Purpose: Your Telegram chat ID to receive messages            │
│  Get from: @userinfobot on Telegram                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Setting Environment Variables Locally

```bash
# Mac/Linux (add to ~/.bashrc or ~/.zshrc for permanent)
export GROQ_API_KEY="gsk_your_key_here"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Windows PowerShell (temporary)
$env:GROQ_API_KEY="gsk_your_key_here"

# Windows Command Prompt (temporary)
set GROQ_API_KEY=gsk_your_key_here
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

### Step 3: Set Environment Variables

```bash
# Set required variables
export GROQ_API_KEY="gsk_your_key_here"

# Optional: For Telegram notifications
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_telegram_chat_id"

# On Windows (PowerShell):
$env:GROQ_API_KEY="gsk_your_key_here"

# On Windows (Command Prompt):
set GROQ_API_KEY=gsk_your_key_here
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

> Easiest deployment - uses Replit's built-in PostgreSQL!

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
│  5. Add PostgreSQL Database:                     │
│     ────────────────────────────────────────     │
│     • Click Database icon (left sidebar)         │
│     • Click "Create database"                    │
│     • Wait ~30 seconds                           │
│     • DATABASE_URL auto-created!                  │
│     ────────────────────────────────────────     │
│                                                      │
│  6. Add Secrets (click 🔐 icon):                 │
│     ────────────────────────────────────────     │
│     GROQ_API_KEY = gsk_your_api_key              │
│     TELEGRAM_BOT_TOKEN = (optional)              │
│     TELEGRAM_CHAT_ID = (optional)               │
│     ADMIN_USERNAME = (optional)                 │
│     ADMIN_PASSWORD = (optional)                  │
│     ────────────────────────────────────────     │
│                                                      │
│  7. Click "Run" (Green button)                   │
│                                                      │
│  8. Get your URL from the preview                 │
│                                                      │
└─────────────────────────────────────────────────────────────┘
```

### What Happens When You Add PostgreSQL:

1. Replit automatically creates `DATABASE_URL` environment variable
2. Your app connects to the database automatically
3. No extra configuration needed!

### Replit Configuration

Your `.replit` should look like this:

```toml
modules = ["web", "python-3.12"]

[deployment]
run = ["gunicorn", "--bind=0.0.0.0:5000", "--workers=1", "--timeout=120", "app:app"]
build = ["pip", "install", "-r", "requirements.txt"]
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
| **Database error on Replit** | Click Database icon → ensure database is active |

### Get Help:

```
┌─────────────────────────────────────────────┐
│           NEED HELP?                        │
├─────────────────────────────────────────────┤
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
- **Hosting**: Replit

---

> Made with ❤️ by Ahmad | © 2026