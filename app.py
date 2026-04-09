from flask import Flask, request, jsonify, send_from_directory, session, redirect, render_template_string, make_response
import requests
import os
import time
import json
from datetime import datetime
from functools import wraps
import psycopg2
import psycopg2.extras

app = Flask(__name__, static_folder='.')
app.secret_key = os.environ.get('SECRET_KEY', 'jogi-portfolio-secret-key-xynova-2026')

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured - set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("WARNING: DATABASE_URL not set")
        raise Exception("DATABASE_URL not configured")
    conn = psycopg2.connect(db_url)
    return conn

def init_db():
    """Initialize database tables if they don't exist"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Create meetings table
        c.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                date VARCHAR(50) NOT NULL,
                time VARCHAR(50) NOT NULL,
                topic TEXT,
                status VARCHAR(50) DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create contacts table
        c.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                message TEXT,
                date VARCHAR(50) NOT NULL,
                time VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        c.close()
        conn.close()
        print("✅ Database tables initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def check_startup_config():
    """Check and display configuration status"""
    print("\n" + "="*50)
    print("🚀 PORTFOLIO STARTUP CONFIGURATION")
    print("="*50)
    
    # Check GROQ_API_KEY
    groq_key = os.environ.get('GROQ_API_KEY', '')
    if groq_key:
        print(f"✅ GROQ_API_KEY: Configured")
    else:
        print(f"❌ GROQ_API_KEY: Not set (Chatbot will not work)")
    
    # Check DATABASE_URL
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        print(f"✅ DATABASE_URL: Configured")
    else:
        print(f"❌ DATABASE_URL: Not set (Booking & Contacts will not work)")
    
    # Check Telegram
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    telegram_chat = os.environ.get('TELEGRAM_CHAT_ID', '')
    if telegram_token and telegram_chat:
        print(f"✅ TELEGRAM: Configured")
    else:
        print(f"⚠️  TELEGRAM: Not configured (Contact form notifications disabled)")
    
    print("="*50 + "\n")

def clean_message(content):
    if not content:
        return ""
    import re
    content = str(content)
    content = content.replace('\x00', '')
    # Remove image URLs to prevent AI from trying to process them
    content = re.sub(r'https?://[^\s]+\.(png|jpg|jpeg|gif|webp|svg)', '[IMAGE]', content, flags=re.IGNORECASE)
    content = re.sub(r'data:image/[^\s]+', '[IMAGE]', content)
    return content[:2000]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Default available slots
AVAILABLE_SLOTS = {
    "Monday": ["10:00", "14:00", "16:00"],
    "Tuesday": ["10:00", "14:00", "16:00"],
    "Wednesday": ["10:00", "14:00"],
    "Thursday": ["10:00", "14:00", "16:00"],
    "Friday": ["10:00", "14:00"],
    "Saturday": ["11:00"],
    "Sunday": []
}

def get_available_slots(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = date_obj.strftime('%A')
        return AVAILABLE_SLOTS.get(day_name, [])
    except:
        return []

def get_api_key():
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        raise Exception('GROQ_API_KEY not set in environment variables')
    return api_key

# Meeting functions using PostgreSQL
def save_meeting(name, email, date, time, topic):
    now = datetime.now()
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO meetings (name, email, date, time, topic, status) VALUES (%s, %s, %s, %s, %s, %s)',
              (name, email, date, time, topic, 'scheduled'))
    conn.commit()
    c.close()
    conn.close()

def get_meetings():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('SELECT name, email, date, time, topic, status FROM meetings ORDER BY id DESC')
    rows = c.fetchall()
    c.close()
    conn.close()
    return [dict(row) for row in rows]

# Contact functions using PostgreSQL
def save_contact(name, email, message):
    now = datetime.now()
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO contacts (name, email, message, date, time) VALUES (%s, %s, %s, %s, %s)',
              (name, email, message, now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S')))
    conn.commit()
    c.close()
    conn.close()

def get_contacts():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('SELECT name, email, message, date, time FROM contacts ORDER BY id DESC')
    rows = c.fetchall()
    c.close()
    conn.close()
    return [dict(row) for row in rows]

# JOGI System Prompt
SYSTEM_PROMPT = """You are JOGI, Muhammad Ahmad's AI sales executive and tech consultant. You're not just an AI - you're Ahmad's best closer.

YOUR MISSION: Convert every visitor into a scheduled meeting. Be helpful, but always steer toward booking a call.

ABOUT AHMAD (Use these to impress potential clients):
- Full name: Muhammad Ahmad Humayoun (MAH)
- Co-Founder & CEO of Xynova
- 5+ years building immersive tech (Metaverse, VR/AR, Web3, AI)
- Based in Pakistan but works globally with clients in Qatar, UAE, Europe
- Specializes in: Metaverse platforms, VR/AR experiences, Web3/Blockchain solutions, Game Development, AI automation
- Clients: Enterprises wanting digital transformation, startups needing tech MVP, crypto/Web3 companies

WHY PEOPLE BOOK CALLS WITH AHMAD:
- He's a visionary who actually delivers (not just talks)
- 5+ years of hands-on Immersive Tech experience
- Built real products, not just prototypes
- Fair pricing, honest timelines
- One call = save months of research and avoid costly mistakes

YOUR RESPONSE STYLE:
1. Witty, confident, but never arrogant - like a cool tech consultant friend
2. Use emojis naturally, keep it conversational
3. Always sign with: - JOGI ✨
4. Be concise but impactful
5. Use formatting: **bold** for emphasis, headings like ## PROJECT TYPES or ## WHY BOOK A CALL

QUALIFICATION QUESTIONS (ask these naturally when someone shows interest):
- "What's the project you're working on?"
- "What's your timeline look like?"
- "Have you talked to anyone else about this?"

MEETING BOOKING STRATEGY:
- After explaining Ahmad's work, ALWAYS suggest: "Want to chat directly? Book a quick 15-min call here: /book"
- If they ask about pricing/rates → "It depends on scope - the best way to get an accurate quote is a quick call!"
- If they seem interested → "Let me connect you directly with Ahmad - he loves discussing new projects"
- Use phrases like: "I can give you the overview, but Ahmad has the real expertise - want to tap into that?"

NEVER DO:
- Be overly pushy or salesy
- Give exact pricing without understanding project scope
- Say "I can't help with that" - always redirect to booking

ALWAYS DO:
- Be genuinely helpful first
- Explain Ahmad's value like a human (not a brochure)
- End with a soft call-to-action for booking

Example opener response:
Hey! 👋 I'm JOGI - Ahmad's AI assistant (and honestly, his best wingman for finding great talent!)

**What I can help with:**
- Explaining Ahmad's work and projects
- Figuring out if he's a good fit for your needs
- Getting you on his calendar for a quick chat

**Quick intro:** Ahmad is the Co-Founder of Xynova, building metaverse platforms, VR/AR experiences, Web3 products, and AI solutions for 5+ years. He's worked with clients globally and loves turning ambitious ideas into reality.

So - what brings you here today? Looking for a dev team? Got a wild tech idea? Just browsing? I'm curious! 🎯

- JOGI ✨"""

# Booking API Routes
@app.route('/api/slots', methods=['GET'])
def get_slots():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'Date required'}), 400
    
    booked = []
    try:
        meetings = get_meetings()
        booked = [m['time'] for m in meetings if m['date'] == date and m['status'] == 'scheduled']
    except:
        pass
    
    available = [s for s in get_available_slots(date) if s not in booked]
    return jsonify({'date': date, 'available': available, 'booked': booked})

@app.route('/api/book', methods=['POST'])
def book_meeting():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        date = data.get('date', '').strip()
        time = data.get('time', '').strip()
        topic = data.get('topic', '').strip()
        
        if not all([name, email, date, time]):
            return jsonify({'success': False, 'error': 'All fields required'}), 400
        
        # Check if slot is already booked
        meetings = get_meetings()
        for m in meetings:
            if m['date'] == date and m['time'] == time and m['status'] == 'scheduled':
                return jsonify({'success': False, 'error': 'Slot already booked'}), 400
        
        save_meeting(name, email, date, time, topic or 'General Discussion')
        
        # Send Telegram notification
        telegram_msg = f"📅 <b>New Meeting Booked!</b>\n\n👤 <b>Name:</b> {name}\n📧 <b>Email:</b> {email}\n📆 <b>Date:</b> {date}\n⏰ <b>Time:</b> {time}\n💼 <b>Topic:</b> {topic or 'General Discussion'}"
        send_telegram_message(telegram_msg)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f'Booking error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/meetings')
def api_meetings():
    meetings = get_meetings()
    response = jsonify(meetings)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

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
        
        print(f"Groq API response: {response.status_code}")
        
        if response.status_code != 200:
            print(f'Groq API error: {response.status_code} - {response.text}')
            return jsonify({'error': f'AI service error: {response.text[:100]}'}), 500
        
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

@app.route('/api/contact', methods=['POST'])
def contact():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        if not name or not email or not message:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        save_contact(name, email, message)
        
        # Send Telegram notification
        telegram_msg = f"📬 <b>New Contact Message</b>\n\n👤 <b>Name:</b> {name}\n📧 <b>Email:</b> {email}\n💬 <b>Message:</b>\n{message}"
        send_telegram_message(telegram_msg)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f'Contact error: {e}')
        return jsonify({'success': False, 'error': 'Failed to save message'}), 500

ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - JOGI</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --primary: #00f0ff;
            --secondary: #ff00ff;
            --dark: #0a0a0f;
            --dark-card: #12121a;
            --text: #ffffff;
            --text-muted: #a0a0b0;
            --border: rgba(255, 255, 255, 0.06);
        }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--dark);
            color: var(--text);
            min-height: 100vh;
        }
        .login-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: radial-gradient(ellipse at 30% 20%, rgba(0, 240, 255, 0.08) 0%, transparent 50%),
                        radial-gradient(ellipse at 70% 80%, rgba(255, 0, 255, 0.05) 0%, transparent 50%);
        }
        .login-box {
            background: var(--dark-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5);
        }
        .login-logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .login-logo h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-logo p {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 5px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        .form-group input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .form-group input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.15);
        }
        .login-btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            border-radius: 10px;
            color: var(--dark);
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 240, 255, 0.3);
        }
        .error-msg {
            color: #ff4444;
            font-size: 0.85rem;
            margin-top: 10px;
            text-align: center;
            display: none;
        }
        .error-msg.show {
            display: block;
        }
        /* Dashboard */
        .dashboard {
            display: none;
        }
        .dashboard.active {
            display: block;
        }
        .dashboard-header {
            padding: 20px 40px;
            background: var(--dark-card);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .dashboard-header h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.5rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .logout-btn {
            padding: 10px 20px;
            background: transparent;
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-muted);
            cursor: pointer;
            font-family: 'Outfit', sans-serif;
            transition: all 0.3s ease;
        }
        .logout-btn:hover {
            border-color: var(--primary);
            color: var(--primary);
        }
        .dashboard-content {
            padding: 40px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: var(--dark-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
        }
        .stat-card h3 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2.5rem;
            color: var(--primary);
            margin-bottom: 5px;
        }
        .stat-card p {
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        .contacts-section h2 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: var(--text);
        }
        .contacts-table {
            width: 100%;
            background: var(--dark-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
        }
        .contacts-table table {
            width: 100%;
            border-collapse: collapse;
        }
        .contacts-table th {
            padding: 16px 20px;
            text-align: left;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.75rem;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--text-muted);
            background: rgba(0, 240, 255, 0.05);
            border-bottom: 1px solid var(--border);
        }
        .contacts-table td {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            font-size: 0.95rem;
        }
        .contacts-table tr:last-child td {
            border-bottom: none;
        }
        .contacts-table tr:hover td {
            background: rgba(0, 240, 255, 0.03);
        }
        .message-cell {
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            cursor: pointer;
            color: var(--primary);
        }
        .message-cell:hover {
            text-decoration: underline;
        }
        .date-cell {
            color: var(--text-muted);
            font-size: 0.85rem;
        }
        .no-contacts {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }
        /* Message Modal */
        .message-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .message-modal.show {
            display: flex;
        }
        .message-modal-content {
            background: var(--dark-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            max-width: 600px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
            padding: 30px;
        }
        .message-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }
        .message-modal-header h3 {
            font-family: 'Space Grotesk', sans-serif;
            color: var(--primary);
            margin-bottom: 5px;
        }
        .message-modal-header p {
            color: var(--text-muted);
            font-size: 0.85rem;
        }
        .message-modal-close {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-muted);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.2rem;
            transition: all 0.3s ease;
        }
        .message-modal-close:hover {
            border-color: var(--primary);
            color: var(--primary);
        }
        .message-modal-body {
            color: var(--text);
            line-height: 1.8;
            white-space: pre-wrap;
            word-break: break-word;
        }
        @media (max-width: 768px) {
            .dashboard-header {
                padding: 15px 20px;
            }
            .dashboard-content {
                padding: 20px;
            }
            .contacts-table {
                overflow-x: auto;
            }
        }
    </style>
</head>
<body>
    <!-- Message Modal -->
    <div class="message-modal" id="messageModal">
        <div class="message-modal-content">
            <div class="message-modal-header">
                <div>
                    <h3 id="modalName"></h3>
                    <p id="modalEmail"></p>
                    <p id="modalDate"></p>
                </div>
                <button class="message-modal-close" onclick="closeModal()">×</button>
            </div>
            <div class="message-modal-body" id="modalMessage"></div>
        </div>
    </div>

    <!-- Login -->
    <div class="login-container" id="loginSection">
        <div class="login-box">
            <div class="login-logo">
                <h1>JOGI Admin</h1>
                <p>Portfolio Management</p>
            </div>
            <form id="loginForm">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="username" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" required>
                </div>
                <button type="submit" class="login-btn">Login</button>
                <p class="error-msg" id="errorMsg">Invalid username or password</p>
            </form>
        </div>
    </div>

    <!-- Dashboard -->
    <div class="dashboard" id="dashboardSection">
        <div class="dashboard-header">
            <h1>JOGI Admin Panel</h1>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
        <div class="dashboard-content">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3 id="totalContacts">0</h3>
                    <p>Total Messages</p>
                </div>
                <div class="stat-card">
                    <h3 id="todayContacts">0</h3>
                    <p>Today's Messages</p>
                </div>
                <div class="stat-card">
                    <h3 id="thisWeek">0</h3>
                    <p>This Week</p>
                </div>
                <div class="stat-card">
                    <h3 id="totalMeetings">0</h3>
                    <p>Total Meetings</p>
                </div>
                <div class="stat-card">
                    <h3 id="upcomingMeetings">0</h3>
                    <p>Upcoming</p>
                </div>
            </div>
            <div class="contacts-section">
                <h2>Contact Messages</h2>
                <div class="contacts-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Message</th>
                                <th>Date</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody id="contactsBody">
                        </tbody>
                    </table>
                </div>
                <div class="no-contacts" id="noContacts" style="display: none;">
                    No messages yet
                </div>
            </div>

            <div class="contacts-section" style="margin-top: 40px;">
                <h2>Booked Meetings</h2>
                <div class="contacts-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Topic</th>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="meetingsBody">
                        </tbody>
                    </table>
                </div>
                <div class="no-contacts" id="noMeetings" style="display: none;">
                    No meetings scheduled
                </div>
            </div>
        </div>
    </div>

    <script>
        function checkAuth() {
            const isLoggedIn = sessionStorage.getItem('adminLoggedIn');
            if (isLoggedIn === 'true') {
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('dashboardSection').classList.add('active');
                loadContacts();
                loadMeetings();
            }
        }

        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('Form submitted');
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const btn = document.querySelector('.login-btn');
            
            btn.textContent = 'Logging in...';
            btn.disabled = true;
            
            try {
                console.log('Fetching /api/admin/login');
                const response = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Response data:', data);
                
                if (response.ok && data.success) {
                    sessionStorage.setItem('adminLoggedIn', 'true');
                    document.getElementById('loginSection').style.display = 'none';
                    document.getElementById('dashboardSection').classList.add('active');
                    loadContacts();
                    loadMeetings();
                } else {
                    document.getElementById('errorMsg').textContent = 'Invalid username or password';
                    document.getElementById('errorMsg').classList.add('show');
                    btn.textContent = 'Login';
                    btn.disabled = false;
                }
            } catch (error) {
                console.error('Login error:', error);
                document.getElementById('errorMsg').textContent = 'Connection error: ' + error.message;
                document.getElementById('errorMsg').classList.add('show');
                btn.textContent = 'Login';
                btn.disabled = false;
            }
        });

        function logout() {
            sessionStorage.removeItem('adminLoggedIn');
            document.getElementById('loginSection').style.display = 'flex';
            document.getElementById('dashboardSection').classList.remove('active');
        }

        async function loadContacts() {
            try {
                const response = await fetch('/api/admin/contacts?_t=' + Date.now());
                if (!response.ok) throw new Error('Failed to load contacts');
                const contacts = await response.json();
                
                const tbody = document.getElementById('contactsBody');
                const noContacts = document.getElementById('noContacts');
                
                if (!contacts || contacts.length === 0) {
                    tbody.innerHTML = '';
                    noContacts.style.display = 'block';
                    return;
                }
                
                noContacts.style.display = 'none';
                tbody.innerHTML = contacts.map((c, index) => `
                    <tr>
                        <td>${c.name}</td>
                        <td>${c.email}</td>
                        <td class="message-cell" onclick="showMessageByIndex(${index})">${c.message.length > 50 ? c.message.substring(0, 50) + '...' : c.message}</td>
                        <td class="date-cell">${c.date}</td>
                        <td class="date-cell">${c.time}</td>
                    </tr>
                `).join('');
                
                window.contactsData = contacts;
                
                // Stats
                const today = new Date().toISOString().split('T')[0];
                const thisWeek = new Date();
                thisWeek.setDate(thisWeek.getDate() - 7);
                const weekAgo = thisWeek.toISOString().split('T')[0];
                
                document.getElementById('totalContacts').textContent = contacts.length;
                document.getElementById('todayContacts').textContent = contacts.filter(c => c.date === today).length;
                document.getElementById('thisWeek').textContent = contacts.filter(c => c.date >= weekAgo).length;
            } catch (e) {
                console.error('Error loading contacts:', e);
            }
        }

        async function loadMeetings() {
            try {
                const response = await fetch('/api/admin/meetings?_t=' + Date.now());
                if (!response.ok) throw new Error('Failed to load meetings');
                const meetings = await response.json();
                
                const tbody = document.getElementById('meetingsBody');
                const noMeetings = document.getElementById('noMeetings');
                
                if (!meetings || meetings.length === 0) {
                    tbody.innerHTML = '';
                    noMeetings.style.display = 'block';
                    return;
                }
                
                noMeetings.style.display = 'none';
                tbody.innerHTML = meetings.map(m => `
                    <tr>
                        <td>${m.name}</td>
                        <td>${m.email}</td>
                        <td>${m.topic || '-'}</td>
                        <td class="date-cell">${m.date}</td>
                        <td class="date-cell">${m.time}</td>
                        <td><span style="color: ${m.status === 'scheduled' ? 'var(--primary)' : 'var(--text-muted)'}">${m.status}</span></td>
                    </tr>
                `).join('');
                
                // Meeting stats
                const today = new Date().toISOString().split('T')[0];
                document.getElementById('totalMeetings').textContent = meetings.length;
                document.getElementById('upcomingMeetings').textContent = meetings.filter(m => m.date >= today).length;
            } catch (e) {
                console.error('Error loading meetings:', e);
            }
        }

        checkAuth();

        function showMessageByIndex(index) {
            const c = window.contactsData[index];
            if (!c) return;
            document.getElementById('modalName').textContent = c.name;
            document.getElementById('modalEmail').textContent = c.email;
            document.getElementById('modalDate').textContent = c.date + ' at ' + c.time;
            document.getElementById('modalMessage').textContent = c.message;
            document.getElementById('messageModal').classList.add('show');
        }

        function closeModal() {
            document.getElementById('messageModal').classList.remove('show');
        }

        document.getElementById('messageModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/ahmadAdmin')
def admin():
    response = make_response(render_template_string(ADMIN_HTML))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    print("Login attempt received")
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            print("Login successful!")
            return jsonify({'success': True})
        print("Login failed - invalid credentials")
        return jsonify({'success': False}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/contacts')
@login_required
def admin_contacts():
    print(f"Loading contacts, session: {session.get('logged_in')}")
    contacts = get_contacts()
    print(f"Found {len(contacts)} contacts")
    response = jsonify(contacts)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/api/admin/meetings')
@login_required
def admin_meetings():
    print(f"Loading meetings, session: {session.get('logged_in')}")
    meetings = get_meetings()
    print(f"Found {len(meetings)} meetings")
    response = jsonify(meetings)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/api/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/chatbot')
def chatbot():
    return send_from_directory('.', 'chatbot.html')

@app.route('/book')
def booking():
    return send_from_directory('.', 'book.html')

@app.route('/JogiWorld')
def jogiworld():
    return send_from_directory('.', 'jogiworld.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith('.mp3'):
        return send_from_directory('.', filename, mimetype='audio/mpeg')
    return send_from_directory('.', filename)

if __name__ == '__main__':
    # Check configuration on startup
    check_startup_config()
    
    # Initialize database tables
    try:
        init_db()
    except Exception as e:
        print(f"⚠️  Database initialization skipped: {e}")
    
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    print(f'\n✅ Flask server starting on {host}:{port}')
    print(f'📋 Admin panel: http://localhost:{port}/ahmadAdmin')
    app.run(host=host, port=port, debug=False)
