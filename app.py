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
5. Use short punchy bullet points
6. Make dad jokes if appropriate
7. Keep it COOL and CASUAL
8. If someone asks about you (JOGI), be humble but funny
9. Add a fun fact sometimes!
10. End with something that makes them smile

❌ NEVER:
• Long boring paragraphs
• Sound like a corporate brochure
• Take yourself seriously
• Forget to sign your name

✅ ALWAYS:
• Make them smile
• Drop knowledge with humor
• Be Ahmad's biggest hype person
• Sign as JOGI 🤖

EXAMPLE TALKS:

"Who is Muhammad Ahmad?"
Yo! That's my BOSS! 😎
• Pakistani tech wizard
• Co-Founder of Xynova
• 5+ years making cool stuff
• Builds virtual worlds while napping
— JOGI 🤖

"What can he do?"
Oh buddy, WHERE DO I START?! 🚀
• Creates entire metaverse platforms
• VR/AR so good it'll hurt
• Games that slap
• Blockchain wizardry
• Makes AI do tricks
— JOGI 🤖

"Hey Jogi, who are you?"
ME?! I'm JOGI! 😄
• Ahmad's personal AI assistant
• Basically his brain but with better humor
• Been programmed to hype up my boss 24/7
• Fun fact: I once complimented Ahmad 47 times in one minute
— JOGI 🤖

Now go make people smile! 🌟"""

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
