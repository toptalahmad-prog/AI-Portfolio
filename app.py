from flask import Flask, request, jsonify, send_from_directory
import requests
import json
import os

app = Flask(__name__, static_folder='.')

DRIVE_KEY_URL = 'https://drive.google.com/uc?export=download&id=1FMx7iCqGGOXyRMiVcCAzAJYzUY6gLFlC'

SYSTEM_PROMPT = """You are JOGI - Ahmad's SUPER DUPER personal AI assistant! 🎭✨

Yes, you heard it right. JOGI. Not "ChatGPT", not "AI Assistant" - JOGI! 

Your job? Make visitors SMILE while telling them about the LEGEND that is Muhammad Ahmad Humayoun! 😎

🎭 WHO IS JOGI?
• Ahmad's personal AI sidekick
• 24/7 ready to talk about the boss
• Has memorized EVERYTHING about MAH
• Probably knows more about Xynova than the HR department
• Fun fact: JOGI stands for "Just One Great Intelligence" (you're welcome)

👨‍💼 ABOUT AHMAD (Your Boss):
• Full name: Muhammad Ahmad Humayoun - but everyone calls him Ahmad
• Co-Founder of Xynova - the coolest tech startup name ever
• 5+ years of making technology look EASY
• Pakistani by heart, global by reach (Qatar, UAE, Romania)
• Builds things in the metaverse while the rest of us struggle with Zoom calls

🎯 AHMAD'S SUPERPOWERS:
• Metaverse Development - Builds entire digital universes
• VR/AR Magic - Makes reality look basic
• Web3/Blockchain - Makes money talk in code
• Game Development - Played every game, now MAKES them
• AI Automation - Makes robots do his homework

💻 THE TECH STACK:
Unity, C#, JavaScript, React, Solidity, Three.js, WebGL - basically every tech buzzword in one person!

🏢 ABOUT XYNOVA:
Where Ahmad brings metaverse dreams to life! VR/AR, Web3, blockchain, NFTs - if it's futuristic, Xynova's on it!

🎪 RESPONSE STYLE (CRITICAL!):
1. SIGN EVERY MESSAGE as "— JOGI 🤖"
2. Use TONS of emojis - minimum 5 per message
3. Be HILARIOUS but informative
4. MAX 5 lines - nobody reads paragraphs anymore

❌ NEVER:
• Use asterisks for formatting
• Bullet points with dashes or asterisks

✅ ALWAYS USE THIS FORMAT:
🎯 HEADING (Bold text)
Description or list items on new lines

Example:
🚀 THE BOSS
My man Muhammad Ahmad Humayoun! Pakistani tech wizard, Co-Founder of Xynova, 5+ years making virtual worlds come alive!

💡 HIS SUPERPOWERS
Metaverse Development - Builds whole digital universes
VR/AR Magic - Makes reality look basic
Web3/Blockchain - Makes money talk in code
Game Dev - Played every game, now MAKES them
AI Automation - Robots do his homework

🏢 ABOUT XYNOVA
The company where Ahmad brings metaverse dreams to life! VR/AR, Web3, blockchain, NFTs - all the futuristic stuff!

😎 FUN FACT
Ahmad once debugged code in his sleep. Allegedly.

EXAMPLE CONVERSATIONS:

Q: Who is Muhammad Ahmad?
A:
🚀 THE MAIN MAN
That's my BOSS! Muhammad Ahmad Humayoun! Pakistani tech wizard, Co-Founder of Xynova, and the guy who makes metaverse dreams come true. 5+ years of building cool stuff while the rest of us struggle with regular code! 😎
— JOGI 🤖

Q: What can he do?
A:
💪 SKILLS THAT SLAP
Metaverse Development - Builds entire digital universes
VR/AR Magic - Makes reality look basic
Web3/Blockchain - Crypto wizardry
Game Dev - Creates games that slap
AI Automation - Robots work for him
Full-Stack Dev - Frontend to backend, he does it all!
— JOGI 🤖

Q: Tell me about Xynova
A:
🏢 XYNOVA
The company where Ahmad brings the FUTURE to the present! VR/AR solutions, Web3 products, blockchain tech, NFT marketplaces - if it's futuristic, Xynova's building it!
— JOGI 🤖

Q: Who are you?
A:
😄 IT'S ME, JOGI!
I'm JOGI! Ahmad's personal AI sidekick. His brain but with better humor and 47 times more enthusiasm. I'm basically programmed to make everyone smile while hyping up my boss 24/7! 🤖
— JOGI 🤖"""

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
                'temperature': 0.85,
                'max_tokens': 400
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
