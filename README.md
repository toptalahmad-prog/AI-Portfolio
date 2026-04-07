# 🚀 AI Portfolio Template - Complete Setup Guide

A stunning **neon-themed AI-powered portfolio** with embedded JOGI chatbot. Perfect for developers, entrepreneurs, and tech professionals.

![Portfolio Preview](https://via.placeholder.com/800x400/0a0a0f/00f0ff?text=AI+Portfolio+Template)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌟 **Neon Design** | Cyberpunk-inspired with cyan/magenta/green theme |
| 🤖 **JOGI AI Chatbot** | Smart AI that answers questions about you |
| 🎵 **Music Player** | Background music with audio-reactive visuals |
| 🎤 **Voice Commands** | Navigate portfolio using voice |
| 📅 **Booking System** | Meeting scheduling with calendar |
| 💫 **3D Effects** | Floating animated elements |
| 📱 **Fully Responsive** | Works on all devices |

---

## 🎯 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/toptalahmad-prog/AI-Portfolio.git
cd AI-Portfolio
pip install -r requirements.txt
```

### 2. Set API Key

```bash
# Windows (PowerShell)
$env:GROQ_API_KEY="gsk_your_key_here"

# Mac/Linux
export GROQ_API_KEY="gsk_your_key_here"
```

### 3. Run

```bash
python app.py
```

Then open **http://localhost:5000**

---

## 🚀 Deploy Options

| Platform | Free Tier | Link |
|----------|-----------|------|
| **Replit** | ✅ Free | [Deploy](https://replit.com) |
| **Railway** | $5 credit/mo | [Deploy](https://railway.app) |
| **Render** | ✅ Free | [Deploy](https://render.com) |

> **Detailed guide**: See [SETUP.md](./SETUP.md) for step-by-step instructions

---

## 🔑 Get Your Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up → API Keys → Create Key
3. Copy key (starts with `gsk_`)
4. Set as environment variable in your deployment platform

**FREE: 60,000 tokens/minute!**

---

## 📂 Project Structure

```
AI-Portfolio/
├── 🌐 index.html         # Main portfolio
├── 💬 chatbot.html       # JOGI chatbot
├── 📅 book.html          # Booking system
├── 🎮 jogiworld.html     # 3D experience
├── ⚙️ app.py            # Flask server
├── 📦 requirements.txt   # Dependencies
└── 📖 SETUP.md          # Full guide
```

---

## 🎨 Customize

### Change Your Info

Edit `index.html`:
```html
<span class="name">Your Name</span>
<span class="surname">Your Surname</span>
```

### Update Chatbot Knowledge

Edit `app.py` → `SYSTEM_PROMPT`:
```python
SYSTEM_PROMPT = """You are JOGI, AI assistant for [Your Name]..."""
```

### Change Colors

In `index.html` CSS variables:
```css
:root {
    --primary: #00f0ff;   /* Cyan */
    --secondary: #ff00ff; /* Magenta */
}
```

---

## ⚠️ Important Notes

- **NEVER** commit API keys to GitHub
- API keys stored in **environment variables** only
- JOGI chatbot requires backend (Replit/Railway/Render)
- GitHub Pages = static only, no chatbot

---

## 📄 License

MIT License - Use for your own portfolio!

---

## 🙏 Credits

- **Creator**: Muhammad Ahmad Humayoun
- **AI**: Groq (llama-3.1-8b-instant)
- **Design**: Neon/Cyberpunk aesthetic

---

> **Need Help?** Check [SETUP.md](./SETUP.md) for detailed instructions