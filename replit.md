# 🚀 AI Portfolio Template - Replit Setup Guide

## Overview
A neon-themed AI-powered portfolio website with embedded JOGI chatbot. This guide covers deploying on Replit.

## Architecture
- **Backend**: Python Flask server (`app.py`)
- **Frontend**: Vanilla HTML/CSS/JS (`index.html`, `chatbot.html`)
- **Database**: Neon PostgreSQL (free tier)
- **AI**: Groq API (llama-3.1-8b-instant model)

## Project Structure
```
├── app.py              # Flask server
├── index.html          # Main portfolio
├── chatbot.html        # JOGI chatbot
├── book.html           # Meeting booking
├── jogiworld.html      # 3D experience
├── requirements.txt    # Python dependencies
├── .replit            # Replit configuration
└── replit.md          # This file
```

---

## ⚡ Quick Setup on Replit

### Step 1: Import from GitHub
1. Go to [replit.com](https://replit.com)
2. Click **"+ Create Replit"**
3. Select **"Import from GitHub"**
4. Choose this repository

### Step 2: Add Environment Secrets
Click the **🔐 (Secrets)** icon in the sidebar and add:

| Secret | Value | Required |
|--------|-------|----------|
| `GROQ_API_KEY` | Your Groq API key | ✅ Yes |
| `NEON_DATABASE_URL` | Your Neon database URL | ✅ Yes |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Optional |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Optional |

#### Getting Your Groq API Key:
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up → API Keys → Create Key
3. Copy the key (starts with `gsk_`)

#### Getting Your Neon Database URL:
1. Go to [neon.tech](https://neon.tech)
2. Create a new project
3. Go to **Connection Details**
4. Copy the connection string
5. Add `?sslmode=require` at the end

### Step 3: Run
Click the **Run** button (green, top center)

---

## 🚀 Deployment

### Development
- Click **Run** → runs `python app.py` on port 5000
- Access at the preview URL

### Production
The `.replit` file configures gunicorn for production:
```
gunicorn --bind=0.0.0.0:5000 --workers=1 --timeout=120 app:app
```

---

## 📋 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GROQ_API_KEY` | AI chatbot API key | `gsk_xxxxxxxx` |
| `NEON_DATABASE_URL` | Neon PostgreSQL URL | `postgresql://...` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot for notifications | `123456:ABC-DEF` |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for notifications | `123456789` |
| `SECRET_KEY` | Flask session secret | Optional |
| `ADMIN_USERNAME` | Admin panel username | Optional |
| `ADMIN_PASSWORD` | Admin panel password | Optional |

---

## 🔧 Features

| Feature | Description |
|---------|-------------|
| 🤖 **JOGI AI Chatbot** | Smart AI that answers questions |
| 📅 **Meeting Booking** | Schedule meetings with calendar |
| 📧 **Contact Form** | Get visitor messages via Telegram |
| 🎵 **Music Player** | Background music with visuals |
| 🎤 **Voice Commands** | Navigate using voice |

---

## 🐛 Troubleshooting

### Chatbot not working?
- Check `GROQ_API_KEY` is set in Secrets
- Check server logs for errors

### Booking/Contacts not working?
- Check `NEON_DATABASE_URL` is set correctly
- Ensure Neon DB is active

### Telegram not receiving messages?
- Check both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Start a conversation with your bot first

---

## 📄 License

MIT License - Use for your own portfolio!

---

## 🙏 Credits

- **Creator**: Muhammad Ahmad Humayoun
- **AI**: [Groq](https://groq.com)
- **Database**: [Neon](https://neon.tech)