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
        return cachedKey;
    } catch (error) {
        console.error('Failed to fetch API key from Google Drive:', error);
        if (cachedKey) {
            return cachedKey;
        }
        throw new Error('Unable to retrieve API key');
    }
}

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { messages } = req.body;

    if (!messages || !Array.isArray(messages)) {
        return res.status(400).json({ error: 'Invalid request: messages array required' });
    }

    try {
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

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Groq API error:', response.status, errorData);
            return res.status(response.status).json({ 
                error: 'AI service temporarily unavailable' 
            });
        }

        const data = await response.json();
        const assistantMessage = data.choices?.[0]?.message?.content;

        if (!assistantMessage) {
            return res.status(500).json({ error: 'Invalid response from AI' });
        }

        res.status(200).json({ 
            message: assistantMessage,
            usage: data.usage
        });

    } catch (error) {
        console.error('Chat error:', error);
        res.status(500).json({ error: 'Failed to process your request' });
    }
}
