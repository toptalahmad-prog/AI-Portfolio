# 🚀 AI Portfolio Template - Replit Setup Guide

## Overview
A neon-themed AI-powered portfolio website with embedded JOGI chatbot. This guide covers deploying on Replit using Replit's built-in PostgreSQL database.

## Architecture
- **Backend**: Python Flask server (`app.py`)
- **Frontend**: Vanilla HTML/CSS/JS (`index.html`, `chatbot.html`)
- **Database**: PostgreSQL (Replit's built-in)
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

### Step 2: Add PostgreSQL Database
1. Click the **Database** icon (🗄️) in the left sidebar
2. Click **"Create database"** or **"Add PostgreSQL"**
3. Wait ~30 seconds for it to provision

> ✅ Replit automatically creates `DATABASE_URL` environment variable!

### Step 3: Add Secrets
Click the **🔐 (Secrets)** icon in the sidebar and add:

| Secret | Value | Required |
|--------|-------|----------|
| `GROQ_API_KEY` | Your Groq API key | ✅ Yes |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Optional |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Optional |
| `ADMIN_USERNAME` | Dashboard username | Optional |
| `ADMIN_PASSWORD` | Dashboard password | Optional |

### Step 4: Get Your Secrets

#### Groq API Key:
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up → API Keys → Create Key
3. Copy the key (starts with `gsk_`)

#### Telegram Bot (Optional):
1. Open [BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token
4. Get your chat ID from [@userinfobot](https://t.me/userinfobot)

### Step 5: Run
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

> **Note**: `DATABASE_URL` is automatically created when you add PostgreSQL via Replit's Database tool.

| Variable | Description | How to Get |
|----------|-------------|------------|
| `GROQ_API_KEY` | AI chatbot API key | [console.groq.com](https://console.groq.com) |
| `DATABASE_URL` | PostgreSQL (auto) | Click Database icon → Create database |
| `TELEGRAM_BOT_TOKEN` | Telegram bot | @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | @userinfobot on Telegram |
| `ADMIN_USERNAME` | Admin panel username | Set in Secrets (optional) |
| `ADMIN_PASSWORD` | Admin panel password | Set in Secrets (optional) |

---

## 🔧 Features

| Feature | Description |
|---------|-------------|
| 🤖 **JOGI AI Chatbot** | Smart AI that answers questions |
| 📅 **Meeting Booking** | Schedule meetings with calendar |
| 📧 **Contact Form** | Get visitor messages via Telegram |
| 🎵 **Music Player** | Background music with visuals |
| 🎤 **Voice Commands** | Navigate using voice |
| 🗄️ **Database** | Replit's built-in PostgreSQL |

---

## 🐛 Troubleshooting

### Chatbot not working?
- Check `GROQ_API_KEY` is set in Secrets
- Check server logs for errors

### Database not working?
- Click Database icon in left sidebar
- Ensure database is created and active
- `DATABASE_URL` should be auto-created

### Booking/Contacts not working?
- Make sure PostgreSQL is added via Database tool
- Check that database shows as "Active" in the Database panel

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
- **Hosting & Database**: [Replit](https://replit.com)