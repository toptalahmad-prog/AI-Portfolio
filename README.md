# 🚀 AI Portfolio Template

A stunning **neon-themed AI-powered portfolio** with embedded JOGI chatbot. Perfect for developers, entrepreneurs, and tech professionals who want to showcase their work with style.

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
| 🎵 **Music Player** | Background music with audio-reactive visuals |
| 🎤 **Voice Commands** | Navigate using voice |
| 📅 **Booking System** | Meeting scheduling with calendar |
| 💫 **3D Effects** | Floating animated elements |
| 📱 **Responsive** | Works perfectly on all devices |

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Portfolio.git
cd AI-Portfolio
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set Your API Key

> **Get free API key:** [console.groq.com](https://console.groq.com)

```bash
# Mac/Linux
export GROQ_API_KEY="gsk_your_key_here"

# Windows (PowerShell)
$env:GROQ_API_KEY="gsk_your_key_here"
```

### 4️⃣ Run the Server

```bash
python app.py
```

### 5️⃣ Open in Browser

```
🌐 http://localhost:5000
```

---

## 📦 Deployment Options

### Recommended: Replit (Free)

1. Go to **[replit.com](https://replit.com)**
2. Import your GitHub repo
3. Add secret: `GROQ_API_KEY = your_key_here`
4. Click **Run** → Done!

### Other Options

| Platform | Free Tier | Setup Time |
|:---------|:---------:|:----------:|
| [Railway](https://railway.app) | $5/month | 5 min |
| [Render](https://render.com) | ✅ Free | 5 min |

> 📖 **Full guide:** See [SETUP.md](./SETUP.md)

---

## 📂 Project Structure

```
AI-Portfolio/
├── 🌐  index.html         ← Main portfolio page
├── 💬  chatbot.html        ← JOGI AI chatbot
├── 📅  book.html          ← Meeting booking
├── 🎮  jogiworld.html     ← 3D experience
├── ⚙️  app.py             ← Flask server
├── 📦  requirements.txt   ← Python packages
└── 📖  SETUP.md           ← Detailed guide
```

---

## 🎨 Customization

### Change Your Name

In `index.html`, find and edit:
```html
<span class="name">Muhammad Ahmad</span>
<span class="surname">Humayoun</span>
```

### Update AI Knowledge

In `app.py`, edit the `SYSTEM_PROMPT` variable with your info.

### Change Colors

In `index.html` CSS section:
```css
:root {
    --primary: #00f0ff;   /* Change cyan */
    --secondary: #ff00ff; /* Change magenta */
}
```

---

## ⚠️ Important

| Do | Don't |
|:---|:------|
| ✅ Use environment variables for API keys | ❌ Commit API keys to GitHub |
| ✅ Keep your backend running for chatbot | ❌ Expect chatbot on static hosting |
| ✅ Set GROQ_API_KEY in deployment | ❌ Leave it blank |

---

## 📄 License

MIT License - Feel free to use for your own portfolio!

---

## 🙏 Credits

| Credit | Link |
|:-------|:-----|
| Creator | Muhammad Ahmad Humayoun |
| AI | [Groq](https://groq.com) |
| Inspired by | Neon/Cyberpunk design |

---

<div align="center">

**Made with ❤️ by Ahmad**

[Report Bug](https://github.com/toptalahmad-prog/AI-Portfolio/issues) · [Request Feature](https://github.com/toptalahmad-prog/AI-Portfolio/issues)

</div>