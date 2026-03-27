# Muhammad Ahmad Humayoun Portfolio

A stunning neon-themed AI-powered portfolio with embedded chatbot that answers questions about Muhammad Ahmad Humayoun.

## Features

- Modern neon design with cyan/magenta theme
- 3D animated elements and particle effects
- Custom cursor with trail effect
- **AI Chatbot** - Ask questions about Muhammad Ahmad Humayoun
- Fully responsive design

## How It Works

The API key is stored in **Google Drive** and fetched at runtime by Netlify Functions. The key is **never stored in code** or exposed to users.

## Deployment Guide

### 1. Push to GitHub

```bash
git add .
git commit -m "Portfolio with AI chatbot"
git push origin main
```

### 2. Deploy to Netlify

1. Go to [netlify.com](https://netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Connect to GitHub and select your repository
4. Deploy settings:
   - **Build command:** (leave empty)
   - **Publish directory:** (leave empty)
5. Click "Deploy"

### 3. Custom Domain (Optional)

1. Go to Site Settings → Domain Management
2. Add your custom domain
3. Update DNS as instructed

## Project Structure

```
├── index.html                    # Main portfolio
├── netlify/
│   └── functions/
│       └── chat.js             # Serverless function (fetches key from Google Drive)
├── netlify.toml                # Netlify configuration
└── README.md
```

## API Key Setup

The API key is stored in Google Drive and fetched at runtime. To change the key:

1. Upload a new `key.json` file to Google Drive
2. Update the `DRIVE_KEY_URL` in `netlify/functions/chat.js`

## Tech Stack

- HTML5, CSS3, JavaScript (Vanilla)
- Netlify Functions (Serverless Backend)
- Groq API (AI - llama-3.1-8b-instant)

## License

MIT License
