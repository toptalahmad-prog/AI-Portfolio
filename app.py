from flask import Flask, request, jsonify, send_from_directory, session, redirect, render_template_string
import requests
import os
import time
import csv
import json
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='.')
app.secret_key = os.urandom(24)

DRIVE_KEY_URL = 'https://drive.google.com/uc?export=download&id=1FMx7iCqGGOXyRMiVcCAzAJYzUY6gLFlC'

ADMIN_USERNAME = "RamtaxJOGI"
ADMIN_PASSWORD = "AhmadxRamtaxJOGI@123"
CONTACTS_FILE = 'contacts.csv'

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
    if not content:
        return ""
    content = str(content)
    content = content.replace('\x00', '')
    content = ''.join(char for char in content if ord(char) < 65536)
    return content[:2000]

def init_contacts_file():
    if not os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'email', 'message', 'date', 'time'])

def save_contact(name, email, message):
    init_contacts_file()
    now = datetime.now()
    with open(CONTACTS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            int(now.timestamp()),
            name,
            email,
            message,
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S')
        ])

def get_contacts():
    init_contacts_file()
    contacts = []
    with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append(row)
    return list(reversed(contacts))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/ahmadAdmin')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico')

@app.route('/bgMusic1.mp3')
def serve_audio():
    return send_from_directory('.', 'bgMusic1.mp3', mimetype='audio/mpeg')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith('.mp3'):
        return send_from_directory('.', filename, mimetype='audio/mpeg')
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
        </div>
    </div>

    <script>
        function checkAuth() {
            const isLoggedIn = sessionStorage.getItem('adminLoggedIn');
            if (isLoggedIn === 'true') {
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('dashboardSection').classList.add('active');
                loadContacts();
            }
        }

        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                sessionStorage.setItem('adminLoggedIn', 'true');
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('dashboardSection').classList.add('active');
                loadContacts();
            } else {
                document.getElementById('errorMsg').classList.add('show');
            }
        });

        function logout() {
            sessionStorage.removeItem('adminLoggedIn');
            document.getElementById('loginSection').style.display = 'flex';
            document.getElementById('dashboardSection').classList.remove('active');
        }

        async function loadContacts() {
            const response = await fetch('/api/admin/contacts');
            const contacts = await response.json();
            
            const tbody = document.getElementById('contactsBody');
            const noContacts = document.getElementById('noContacts');
            
            if (contacts.length === 0) {
                tbody.innerHTML = '';
                noContacts.style.display = 'block';
                return;
            }
            
            noContacts.style.display = 'none';
            tbody.innerHTML = contacts.map(c => `
                <tr>
                    <td>${c.name}</td>
                    <td>${c.email}</td>
                    <td class="message-cell" title="${c.message}">${c.message}</td>
                    <td class="date-cell">${c.date}</td>
                    <td class="date-cell">${c.time}</td>
                </tr>
            `).join('');
            
            // Stats
            const today = new Date().toISOString().split('T')[0];
            const thisWeek = new Date();
            thisWeek.setDate(thisWeek.getDate() - 7);
            const weekAgo = thisWeek.toISOString().split('T')[0];
            
            document.getElementById('totalContacts').textContent = contacts.length;
            document.getElementById('todayContacts').textContent = contacts.filter(c => c.date === today).length;
            document.getElementById('thisWeek').textContent = contacts.filter(c => c.date >= weekAgo).length;
        }

        checkAuth();
    </script>
</body>
</html>
'''

@app.route('/ahmadAdmin')
def admin():
    return render_template_string(ADMIN_HTML)

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/api/admin/contacts')
@login_required
def admin_contacts():
    contacts = get_contacts()
    return jsonify(contacts)

@app.route('/api/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

if __name__ == '__main__':
    init_contacts_file()
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    print(f'\nFlask server starting on {host}:{port}')
    print(f'Admin panel: http://localhost:{port}/ahmadAdmin')
    app.run(host=host, port=port, debug=False)
