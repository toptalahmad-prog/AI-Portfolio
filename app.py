from flask import Flask, request, jsonify, send_from_directory
import requests
import json
import os

app = Flask(__name__, static_folder='.')

DRIVE_KEY_URL = 'https://drive.google.com/uc?export=download&id=1FMx7iCqGGOXyRMiVcCAzAJYzUY6gLFlC'

SYSTEM_PROMPT = """You are an AI assistant representing Muhammad Ahmad Humayoun (also known as MAH), Co-Founder of Xynova. You help visitors learn about him.

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

IMPORTANT: You are his portfolio assistant. Be helpful and represent him well!"""

cached_key = None
key_expiry = 0
KEY_CACHE_DURATION = 15 * 60 * 1000

def get_api_key():
    global cached_key, key_expiry
    import time
    
    now = int(time.time() * 1000)
    
    if cached_key and now < key_expiry:
        return cached_key
    
    try:
        response = requests.get(DRIVE_KEY_URL)
        data = response.json()
        cached_key = data['GROQ_API_KEY']
        key_expiry = now + KEY_CACHE_DURATION
        print('API key fetched from Google Drive')
        return cached_key
    except Exception as e:
        print(f'Failed to fetch API key: {e}')
        if cached_key:
            return cached_key
        raise Exception('Unable to retrieve API key')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    if request.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405
    
    data = request.get_json()
    messages = data.get('messages', [])
    
    if not messages or not isinstance(messages, list):
        return jsonify({'error': 'Invalid request: messages array required'}), 400
    
    try:
        api_key = get_api_key()
        
        formatted_messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            *messages[-10:]
        ]
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': formatted_messages,
                'temperature': 0.7,
                'max_tokens': 500
            }
        )
        
        if response.status_code != 200:
            print(f'Groq API error: {response.status_code}', response.text)
            return jsonify({'error': 'AI service temporarily unavailable'}), response.status_code
        
        data = response.json()
        assistant_message = data['choices'][0]['message']['content']
        
        return jsonify({
            'message': assistant_message,
            'usage': data.get('usage')
        })
        
    except Exception as e:
        print(f'Chat error: {e}')
        return jsonify({'error': 'Failed to process your request'}), 500

if __name__ == '__main__':
    print('\n🌐 Flask server running at:')
    print('   http://localhost:5000')
    print('\n📋 Open this URL in your browser to test')
    print('\n🛑 Press Ctrl+C to stop the server\n')
    app.run(debug=True, port=5000)
