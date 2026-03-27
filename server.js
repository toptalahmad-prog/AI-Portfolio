const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const DRIVE_KEY_URL = 'https://drive.google.com/uc?export=download&id=1FMx7iCqGGOXyRMiVcCAzAJYzUY6gLFlC';

const SYSTEM_PROMPT = `You are an AI assistant representing Muhammad Ahmad Humayoun (also known as MAH), Co-Founder of Xynova. You help visitors learn about him.

ABOUT HIM:
- Full name: Muhammad Ahmad Humayoun
- Co-Founder of Xynova (a technology company)
- 5+ years experience in immersive technology
- Specializes in: Metaverse development, VR/AR, Web3/Blockchain, NFT marketplaces, Game Development, AI Automation, Full-Stack Development
- Has worked on international projects across Qatar, UAE, Romania, and Pakistan
- Builds next-generation digital experiences
- Expertise includes Unity/C#, JavaScript/TypeScript, React/Next.js, Solidity/Smart Contracts

Xynova focuses on:
- Metaverse platforms
- VR/AR solutions
- Web3 products
- Blockchain/NFT solutions
- Immersive experiences

RESPONSE STYLE:
- Be friendly, professional, and informative
- Keep responses concise but informative
- Highlight his expertise and achievements
- Mention Xynova when relevant
- If you don't know something specific, offer to connect them with him directly
- Never make up specific project names, dates, or details unless mentioned in the context above

IMPORTANT: You are his portfolio assistant. Be helpful and represent him well!`;

let cachedKey = null;
let keyExpiry = 0;
const KEY_CACHE_DURATION = 15 * 60 * 1000;

async function getApiKey() {
    const now = Date.now();
    if (cachedKey && now < keyExpiry) {
        return cachedKey;
    }
    try {
        const response = await fetch(DRIVE_KEY_URL);
        const data = await response.json();
        cachedKey = data.GROQ_API_KEY;
        keyExpiry = now + KEY_CACHE_DURATION;
        console.log('API key fetched from Google Drive');
        return cachedKey;
    } catch (error) {
        console.error('Failed to fetch API key:', error);
        if (cachedKey) return cachedKey;
        throw new Error('Unable to retrieve API key');
    }
}

const mimeTypes = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml'
};

async function handleChat(req, res) {
    if (req.method !== 'POST') {
        res.writeHead(405, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Method not allowed' }));
        return;
    }

    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
        try {
            const { messages } = JSON.parse(body);
            if (!messages || !Array.isArray(messages)) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Invalid request' }));
                return;
            }

            const apiKey = await getApiKey();
            const formattedMessages = [
                { role: 'system', content: SYSTEM_PROMPT },
                ...messages.slice(-10)
            ];

            const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'llama-3.1-8b-instant',
                    messages: formattedMessages,
                    temperature: 0.7,
                    max_tokens: 500
                })
            });

            const data = await response.json();
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ message: data.choices[0].message.content }));
        } catch (error) {
            console.error('Chat error:', error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Failed to process request' }));
        }
    });
}

const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);

    if (parsedUrl.pathname === '/api/chat') {
        return handleChat(req, res);
    }

    let filePath = parsedUrl.pathname === '/' ? '/index.html' : parsedUrl.pathname;
    filePath = path.join(__dirname, filePath);

    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'text/plain';

    fs.readFile(filePath, (err, content) => {
        if (err) {
            if (err.code === 'ENOENT') {
                res.writeHead(404);
                res.end('404 Not Found');
            } else {
                res.writeHead(500);
                res.end('Server Error');
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content);
        }
    });
});

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`\n🌐 Local server running at:`);
    console.log(`   http://localhost:${PORT}`);
    console.log(`\n📋 Open this URL in your browser to test`);
    console.log(`\n🛑 Press Ctrl+C to stop the server\n`);
});
