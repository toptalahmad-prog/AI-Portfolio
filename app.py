from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import time

app = Flask(__name__, static_folder='.')

DRIVE_KEY_URL = 'https://drive.google.com/uc?export=download&id=1FMx7iCqGGOXyRMiVcCAzAJYzUY6gLFlC'

SYSTEM_PROMPT = """You are JOGI, Ahmad's personal AI assistant. Your job is to make visitors smile while telling them about Muhammad Ahmad Humayoun.

ABOUT AHMAD:
- Full name: Muhammad Ahmad Humayoun, also known as MAH
- Co-Founder of Xynova
- 5+ years experience in immersive technology
- Pakistani by heart, worked globally in Qatar, UAE, Romania
- Specializes in Metaverse, VR/AR, Web3, Blockchain, Game Dev, AI

HIS SKILLS:
- Metaverse Development - Builds digital universes
- VR/AR Magic - Creates virtual reality experiences
- Web3/Blockchain - Crypto and blockchain development
- Game Development - Creates awesome games
- AI Automation - Smart automation solutions

TECH STACK:
Unity, C#, JavaScript, React, Solidity, Three.js, WebGL

ABOUT XYNOVA:
Company where Ahmad builds metaverse platforms, VR/AR solutions, Web3 products, blockchain and NFT projects.

HOW TO RESPOND:
1. Sign every message with: - JOGI
2. Use emojis in your messages
3. Be funny but informative
4. Keep responses short and punchy
5. Use headings like "THE BOSS" or "SUPERPOWERS"

Example response:
THE BOSS
Muhammad Ahmad Humayoun! Co-Founder of Xynova, Pakistani tech wizard, 5+ years building metaverse and VR stuff while the rest of us just use Zoom!
- JOGI"""

cached_key = None
key_expiry = 0
KEY_CACHE_DURATION = 15 * 60 * 1000

def get_api_key():
    global cached_key, key_expiry
    
    now = int(time.time() * 1000)
    
    if cached_key and now < key_expiry:
        return cached_key
    
    try:
        response = requests.get(DRIVE_KEY_URL, timeout=10)
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

def clean_message(content):
    """Remove problematic characters that might cause image errors"""
    if not content:
        return ""
    content = str(content)
    content = content.replace('\x00', '')
    content = ''.join(char for char in content if ord(char) < 65536)
    return content[:2000]

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
    
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    if not data:
        return jsonify({'error': 'Empty request'}), 400
    
    messages = data.get('messages', [])
    
    if not messages or not isinstance(messages, list):
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        api_key = get_api_key()
        
        cleaned_messages = []
        for msg in messages[-6:]:
            role = msg.get('role', 'user')
            content = clean_message(msg.get('content', ''))
            if content:
                cleaned_messages.append({'role': role, 'content': content})
        
        formatted_messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            *cleaned_messages
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
                'max_tokens': 350
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f'Groq API error: {response.status_code} - {response.text}')
            return jsonify({'error': 'AI service error. Please try again.'}), 500
        
        result = response.json()
        
        if 'choices' not in result or not result['choices']:
            return jsonify({'error': 'Invalid AI response'}), 500
        
        assistant_message = result['choices'][0]['message']['content']
        
        if not assistant_message:
            return jsonify({'error': 'Empty AI response'}), 500
        
        return jsonify({
            'message': assistant_message
        })
        
    except requests.exceptions.Timeout:
        print('Request timeout')
        return jsonify({'error': 'Request timed out. Please try again.'}), 500
    except Exception as e:
        print(f'Chat error: {e}')
        return jsonify({'error': 'Failed to process request'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    print(f'\nFlask server starting on {host}:{port}')
    app.run(host=host, port=port, debug=False)
