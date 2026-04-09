# 🚀 AI Portfolio Template

A stunning **neon-themed AI-powered portfolio** with embedded JOGI chatbot, meeting booking system, and admin dashboard. Perfect for developers, entrepreneurs, and tech professionals.

---

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0+-black?style=flat&logo=flask)
![Groq](https://img.shields.io/badge/AI-Groq-cyan?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

</div>

---

## ✨ Features

| Feature | Description |
|:--------|:------------|
| 🌟 **Neon Design** | Cyberpunk-inspired with cyan/magenta theme |
| 🤖 **JOGI AI Chatbot** | Smart AI that answers questions about you |
| 📅 **Booking System** | Meeting scheduling with calendar & timezone support |
| 👤 **Admin Dashboard** | Manage contacts, meetings & availability |
| 🕐 **Availability Settings** | Set daily/weekly/monthly time slots |
| 🌍 **Timezone Support** | Visitors see times in their timezone |
| 📧 **Contact Form** | Messages sent to Telegram |
| 🎵 **Music Player** | Background music with audio-reactive visuals |
| 🎤 **Voice Commands** | Navigate using voice |
| 💫 **3D Effects** | Floating animated elements |
| 📱 **Responsive** | Works perfectly on all devices |

---

## 🛠️ Tech Stack

| Component | Technology |
|:----------|:-----------|
| Backend | Python Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | PostgreSQL (Neon) |
| AI | Groq (llama-3.1-8b-instant) |
| Notifications | Telegram Bot |

---

## 📋 What You Need

Before setting up, gather these accounts:

| Service | Purpose | Free? |
|:--------|:---------|:------|
| [Groq](https://console.groq.com) | AI for chatbot | ✅ 60K tokens/min |
| [Neon](https://neon.tech) | PostgreSQL database | ✅ |
| [Telegram Bot](https://t.me/BotFather) | Contact notifications | ✅ |

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Portfolio.git
cd AI-Portfolio
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Environment Variables

```bash
# Required
export GROQ_API_KEY="gsk_your_groq_key"
export DATABASE_URL="postgresql://user:pass@host/neondb?sslmode=require"

# Optional (for Telegram notifications)
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Optional (for admin dashboard)
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your_password"
```

### Step 4: Run Locally

```bash
python app.py
```

### Step 5: Open in Browser

```
🌐 http://localhost:5000
```

---

## ☁️ Deploy to Replit

### Step 1: Import from GitHub
1. Go to **[replit.com](https://replit.com)**
2. Click **"+ Create Replit"**
3. Select **"Import from GitHub"**
4. Choose this repository

### Step 2: Add Secrets (🔐 icon)

| Secret | Value | Required |
|:-------|:-------|:---------|
| `GROQ_API_KEY` | Your Groq API key | ✅ Yes |
| `NEON_URL` | Your Neon PostgreSQL URL | ✅ Yes |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Optional |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Optional |
| `ADMIN_USERNAME` | Dashboard username | Optional |
| `ADMIN_PASSWORD` | Dashboard password | Optional |

### Step 3: Get Your Secrets

#### Groq API Key (Required)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up → API Keys → Create Key
3. Copy key (starts with `gsk_`)

#### Neon Database (Required)
1. Go to [neon.tech](https://neon.tech)
2. Create a new project
3. Go to **Connection Details**
4. Copy the connection string
5. Add `?sslmode=require` at the end

#### Telegram Bot (Optional)
1. Open [BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token
4. Get your chat ID from [@userinfobot](https://t.me/userinfobot)

### Step 4: Run

Click **Run** → Done! 🎉

---

## 🔧 Configuration

### Admin Dashboard

Access at: `/ahmadAdmin`

| Feature | Description |
|:--------|:-------------|
| 👥 **Contacts** | View all contact form submissions |
| 📅 **Meetings** | View all booked meetings |
| ⚙️ **Availability** | Set your available time slots |
| 🌍 **Timezone** | Set your timezone |

### Availability Settings

In the admin dashboard, you can set:

| Mode | Description |
|:-----|:------------|
| 📅 **Daily** | Different hours for each day of the week |
| 📆 **Weekly** | Same hours for all days |
| 📆 **Monthly** | Same hours for all dates in a month |

**Default times**: 11:00 PM, 12:00 AM, 1:00 AM (Pakistan timezone)

### Timezone Support

- Visitors see time slots in their local timezone
- You set your timezone in admin dashboard
- Time difference is displayed to visitors

---

## 📂 Project Structure

```
AI-Portfolio/
├── 🌐  index.html         ← Main portfolio
├── 💬  chatbot.html       ← JOGI AI chatbot
├── 📅  book.html          ← Meeting booking
├── 🎮  jogiworld.html    ← 3D experience
├── ⚙️  app.py            ← Flask server
├── 📦  requirements.txt  ← Python packages
├── 📖  SETUP.md          ← Detailed guide
└── 📖  replit.md         ← Replit deployment guide
```

---

## 🎨 Customization

### Change Your Name

In `index.html`:
```html
<span class="name">Your Name</span>
<span class="surname">Your Surname</span>
```

### Update AI Knowledge

In `app.py`, edit the `SYSTEM_PROMPT` variable.

### Change Colors

In `index.html`:
```css
:root {
    --primary: #00f0ff;   /* Cyan */
    --secondary: #ff00ff; /* Magenta */
}
```

---

## ⚠️ Important Notes

| Do | Don't |
|:---|:------|
| ✅ Use environment variables | ❌ Commit API keys to GitHub |
| ✅ Keep backend running for chatbot | ❌ Expect chatbot on static hosting |
| ✅ Set NEON_URL for database | ❌ Leave database config empty |
| ✅ Use Replit for deployment | ❌ Use GitHub Pages (no backend) |

---

## ❓ Troubleshooting

### Chatbot not working?
- Check `GROQ_API_KEY` is set in Secrets
- Check server logs for errors

### Database not connecting?
- Verify `NEON_URL` is correct
- Check Neon project is active

### Telegram not receiving messages?
- Verify both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Start a conversation with your bot first

### Time slots not showing?
- Go to admin dashboard → Set availability
- Default: 11:00 PM, 12:00 AM, 1:00 AM

---

## 📄 License

MIT License - Feel free to use for your own portfolio!

---

## 🙏 Credits

| Credit | Link |
|:-------|:-----|
| Creator | Muhammad Ahmad Humayoun |
| AI | [Groq](https://groq.com) |
| Database | [Neon](https://neon.tech) |

---

<div align="center">

**Made with ❤️ by Ahmad**

[Report Bug](https://github.com/toptalahmad-prog/AI-Portfolio/issues)

</div>