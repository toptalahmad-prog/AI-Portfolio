# Muhammad Ahmad Humayoun Portfolio

A stunning neon-themed AI-powered portfolio showcasing immersive technology expertise, featuring an embedded AI chatbot that answers questions about Muhammad Ahmad Humayoun.

## Features

- Modern neon design with cyan/magenta theme
- 3D animated elements and particle effects
- Custom cursor with trail effect
- Scroll animations and parallax effects
- **AI Chatbot** - Ask questions about Muhammad Ahmad Humayoun
- Fully responsive design

## Getting Started

### Quick Preview (Local)

1. Clone the repository
2. Open `index.html` in your browser

**Note:** The AI chatbot requires deployment to Vercel to function.

### Deploy to Vercel (Full Setup)

This portfolio uses a serverless API to hide the AI API key. Follow these steps:

#### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

#### 2. Get Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account (14 requests/minute on free tier)
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (you won't see it again)

#### 3. Deploy on Vercel

1. Go to [vercel.com](https://vercel.com)
2. Log in with GitHub
3. Click "Add New Project"
4. Select your repository
5. Click "Deploy"

#### 4. Configure Environment Variable

1. In Vercel dashboard, go to your project
2. Click "Settings" tab
3. Click "Environment Variables"
4. Add:
   - **Name:** `GROQ_API_KEY`
   - **Value:** Your Groq API key
5. Click "Save"

#### 5. Redeploy

1. Go to "Deployments" tab
2. Click the three dots on the latest deployment
3. Select "Redeploy"
4. Wait for deployment to complete

Your portfolio is now live with the AI chatbot!

## Project Structure

```
├── index.html          # Main portfolio page
├── api/
│   └── chat.js         # Serverless API (hides API key)
├── vercel.json         # Vercel configuration
├── .env.example        # Environment variable template
└── README.md
```

## How It Works

1. **Frontend** (`index.html`): Contains the chatbot widget that sends messages to `/api/chat`
2. **Backend** (`api/chat.js`): Vercel serverless function that:
   - Receives messages from the frontend
   - Adds context about Muhammad Ahmad Humayoun
   - Calls Groq API with the hidden API key
   - Returns the response

The API key is stored in Vercel's environment variables and never exposed to the frontend or pushed to GitHub.

## Customization

Edit `index.html` to update:
- Personal information
- Projects and experience
- Skills and expertise
- Social links

Edit `api/chat.js` to update:
- AI chatbot's knowledge about you (SYSTEM_PROMPT variable)

## Tech Stack

- HTML5, CSS3, JavaScript (Vanilla)
- Vercel (Hosting + Serverless Functions)
- Groq API (AI Chatbot - llama-3.1-8b-instant model)

## License

MIT License - feel free to use and modify!
