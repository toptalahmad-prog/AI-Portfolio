from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    session,
    redirect,
    render_template_string,
    make_response,
)
from flask_cors import CORS
import requests
import os
import time
import json
from datetime import datetime, timedelta
from functools import wraps
import psycopg2
import psycopg2.extras
import re
from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder=".")
app.secret_key = os.environ.get("SECRET_KEY", "jogi-portfolio-secret-key-xynova-2026")

# Rate limiting for chat API
RATE_LIMIT = 10  # max requests
RATE_WINDOW = 60  # seconds
chat_requests = defaultdict(list)

# Enable CORS for all routes
CORS(app)

# ==========================================
# DATABASE CONFIGURATION & VALIDATION
# ==========================================

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


# Validate DATABASE_URL format on startup
def validate_database_url():
    if not DATABASE_URL:
        return False, "DATABASE_URL not set"

    # Check it starts with postgres:// or postgresql://
    if not (
        DATABASE_URL.startswith("postgres://")
        or DATABASE_URL.startswith("postgresql://")
    ):
        return (
            False,
            f"Invalid DATABASE_URL format. Must start with 'postgres://' or 'postgresql://', got: {DATABASE_URL[:20]}...",
        )

    # Check it contains @ (has password/host)
    if "@" not in DATABASE_URL:
        return (
            False,
            "Invalid DATABASE_URL - missing @ (should contain user:password@host)",
        )

    return True, "Valid"


is_valid_db, db_validation_msg = validate_database_url()

# ==========================================
# TELEGRAM BOT CONFIGURATION
# ==========================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_telegram_message(message):
    """Send message via Telegram Bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured - set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


# Admin credentials - Replit secrets fix
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "") or os.environ.get(
    "ADMIN_USER", ""
)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "") or os.environ.get(
    "ADMIN_PASS", ""
)

# Database available flag - for graceful fallback
DATABASE_AVAILABLE = False
DB_INIT_MESSAGE = ""


def get_db():
    """Get database connection with proper error handling"""
    if not is_valid_db:
        raise Exception(f"Database not configured: {db_validation_msg}")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Database connection failed: {str(e)[:100]}")
    except Exception as e:
        raise Exception(f"Database error: {str(e)[:100]}")


def verify_db_connection():
    """Test database connection on startup"""
    global DATABASE_AVAILABLE, DB_INIT_MESSAGE
    try:
        if not is_valid_db:
            DATABASE_AVAILABLE = False
            DB_INIT_MESSAGE = db_validation_msg
            print(f"⚠️  Database: {DB_INIT_MESSAGE}")
            return False

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT 1")
        c.close()
        conn.close()
        DATABASE_AVAILABLE = True
        DB_INIT_MESSAGE = "Connected successfully"
        print(f"✅ Database: Connected and ready")
        return True
    except Exception as e:
        DATABASE_AVAILABLE = False
        DB_INIT_MESSAGE = str(e)[:100]
        print(f"❌ Database connection failed: {DB_INIT_MESSAGE}")
        return False


def init_db():
    """Initialize database tables if they don't exist"""
    if not is_valid_db:
        print(f"⚠️  Database initialization skipped: {db_validation_msg}")
        return False

    try:
        conn = get_db()
        c = conn.cursor()

        # Create meetings table
        c.execute("""
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
        """)

        # Create contacts table
        c.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                message TEXT,
                date VARCHAR(50) NOT NULL,
                time VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create availability table
        c.execute("""
            CREATE TABLE IF NOT EXISTS availability (
                id SERIAL PRIMARY KEY,
                setting_type VARCHAR(20) NOT NULL DEFAULT 'weekly',
                day_of_week VARCHAR(10),
                specific_date DATE,
                time_slots TEXT NOT NULL DEFAULT '[]',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create settings table for timezone configuration
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                setting_key VARCHAR(50) UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert default availability if empty
        c.execute("SELECT COUNT(*) FROM availability")
        if c.fetchone()[0] == 0:
            default_slots = '["23:00", "00:00", "01:00"]'
            days = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            for day in days:
                c.execute(
                    "INSERT INTO availability (setting_type, day_of_week, time_slots) VALUES (%s, %s, %s)",
                    ("daily", day, default_slots),
                )

        c.execute("SELECT COUNT(*) FROM availability WHERE setting_type = 'weekly'")
        if c.fetchone()[0] == 0:
            c.execute(
                "INSERT INTO availability (setting_type, time_slots) VALUES (%s, %s)",
                ("weekly", '["23:00", "00:00", "01:00"]'),
            )

        c.execute("SELECT COUNT(*) FROM settings")
        if c.fetchone()[0] == 0:
            c.execute(
                "INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)",
                ("owner_timezone", "Asia/Karachi"),
            )
            c.execute(
                "INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)",
                ("availability_mode", "daily"),
            )

            # Insert default availability (daily mode - each day)
            days = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            for day in days:
                c.execute(
                    """
                    INSERT INTO availability (setting_type, day_of_week, time_slots, is_active)
                    VALUES (%s, %s, %s, TRUE)
                """,
                    ("daily", day, '["23:00", "00:00", "01:00"]'),
                )

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
    print("\n" + "=" * 50)
    print("🚀 PORTFOLIO STARTUP CONFIGURATION")
    print("=" * 50)

    # Check GROQ_API_KEY
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        print(f"✅ GROQ_API_KEY: Configured")
    else:
        print(f"❌ GROQ_API_KEY: Not set (Chatbot will not work)")

    # Check DATABASE_URL
    if is_valid_db:
        print(f"✅ DATABASE_URL: Valid format")
    else:
        print(f"❌ DATABASE_URL: {db_validation_msg}")

    # Check database connection
    if DATABASE_AVAILABLE:
        print(f"✅ Database: Connected and ready")
    else:
        print(f"⚠️  Database: {DB_INIT_MESSAGE}")

    # Check Telegram
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    telegram_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if telegram_token and telegram_chat:
        print(f"✅ TELEGRAM: Configured")
    else:
        print(f"⚠️  TELEGRAM: Not configured (Contact form notifications disabled)")

    print("=" * 50 + "\n")


def clean_message(content):
    if not content:
        return ""
    import re

    content = str(content)
    content = content.replace("\x00", "")
    # Remove image URLs to prevent AI from trying to process them
    content = re.sub(
        r"https?://[^\s]+\.(png|jpg|jpeg|gif|webp|svg)",
        "[IMAGE]",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(r"data:image/[^\s]+", "[IMAGE]", content)
    return content[:2000]


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Not authenticated"}), 401
        return f(*args, **kwargs)

    return decorated_function


def check_rate_limit(ip):
    """Check if IP has exceeded rate limit. Returns (allowed, remaining_requests)"""
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_WINDOW)

    # Clean old entries
    chat_requests[ip] = [t for t in chat_requests[ip] if t > window_start]

    if len(chat_requests[ip]) >= RATE_LIMIT:
        return False, 0

    chat_requests[ip].append(now)
    return True, RATE_LIMIT - len(chat_requests[ip])


# Default available slots
AVAILABLE_SLOTS = {
    "Monday": ["23:00", "00:00", "01:00"],
    "Tuesday": ["23:00", "00:00", "01:00"],
    "Wednesday": ["23:00", "00:00", "01:00"],
    "Thursday": ["23:00", "00:00", "01:00"],
    "Friday": ["23:00", "00:00", "01:00"],
    "Saturday": ["23:00", "00:00", "01:00"],
    "Sunday": ["23:00", "00:00", "01:00"],
}


def get_owner_timezone():
    """Get the owner's timezone from settings"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT setting_value FROM settings WHERE setting_key = 'owner_timezone'"
        )
        result = c.fetchone()
        print(f"[TIMEZONE] Query result: {result}")
        c.close()
        conn.close()
        tz = result[0] if result else "Asia/Karachi"
        print(f"[TIMEZONE] Returned: {tz}")
        return tz
    except Exception as e:
        print(f"[TIMEZONE] Error: {e}")
        return "Asia/Karachi"


def get_availability_mode():
    """Get the availability mode (daily, weekly, monthly)"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT setting_value FROM settings WHERE setting_key = 'availability_mode'"
        )
        result = c.fetchone()
        print(f"[MODE] Query result: {result}")
        c.close()
        conn.close()
        mode = result[0] if result else "daily"
        print(f"[MODE] Returned mode: {mode}")
        return mode
    except Exception as e:
        print(f"[MODE] Error getting mode: {e}")
        return "daily"


def get_available_slots(date_str):
    """Get available slots for a specific date, considering the availability mode"""
    print(f"[AVAILABILITY] Getting slots for: {date_str}")
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = date_obj.strftime("%A")
        date_iso = date_obj.strftime("%Y-%m-%d")
        print(f"[AVAILABILITY] Day: {day_name}, ISO: {date_iso}")

        conn = get_db()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check availability mode
        mode = get_availability_mode()
        print(f"[AVAILABILITY] Mode from DB: '{mode}'")

        if mode == "monthly":
            print("[AVAILABILITY] Checking monthly mode")
            # First try specific date
            c.execute(
                "SELECT time_slots FROM availability WHERE setting_type = 'monthly' AND specific_date = %s AND is_active = TRUE",
                (date_iso,),
            )
            result = c.fetchone()
            print(f"[AVAILABILITY] Monthly result: {result}")
            if result:
                c.close()
                conn.close()
                return json.loads(result["time_slots"])
            return []

        if mode == "weekly":
            print("[AVAILABILITY] Checking weekly mode")
            # Get the week's start date (Monday)
            week_start = date_obj - timedelta(days=date_obj.weekday())
            week_start_iso = week_start.strftime("%Y-%m-%d")

            # Try specific week first (stored with specific_date = week start)
            c.execute(
                "SELECT time_slots FROM availability WHERE setting_type = 'weekly' AND specific_date = %s AND is_active = TRUE",
                (week_start_iso,),
            )
            result = c.fetchone()
            print(f"[AVAILABILITY] Weekly result (specific week): {result}")
            if result:
                c.close()
                conn.close()
                return json.loads(result["time_slots"])

            # Fall back to generic weekly entry
            c.execute(
                "SELECT time_slots FROM availability WHERE setting_type = 'weekly' AND day_of_week IS NULL AND specific_date IS NULL AND is_active = TRUE LIMIT 1"
            )
            result = c.fetchone()
            print(f"[AVAILABILITY] Weekly result (generic): {result}")
            c.close()
            conn.close()
            if result:
                return json.loads(result["time_slots"])
            return []

        # Daily mode - check specific date first, then fall back to day of week
        print(f"[AVAILABILITY] Checking daily mode for {date_iso}")

        # Try specific date first
        c.execute(
            "SELECT time_slots FROM availability WHERE setting_type = 'daily' AND specific_date = %s AND is_active = TRUE",
            (date_iso,),
        )
        result = c.fetchone()
        print(f"[AVAILABILITY] Daily result (specific date): {result}")

        if result:
            c.close()
            conn.close()
            slots = json.loads(result["time_slots"])
            print(f"[AVAILABILITY] Returning {len(slots)} slots from specific date")
            return slots

        # Fall back to day of week
        print(f"[AVAILABILITY] Trying day of week: {day_name}")
        c.execute(
            "SELECT time_slots FROM availability WHERE setting_type = 'daily' AND day_of_week = %s AND is_active = TRUE",
            (day_name,),
        )
        result = c.fetchone()
        print(f"[AVAILABILITY] Daily result (day of week): {result}")
        c.close()
        conn.close()

        if result:
            slots = json.loads(result["time_slots"])
            print(f"[AVAILABILITY] Returning {len(slots)} slots from day of week")
            return slots

        print("[AVAILABILITY] No slots found, returning empty array")
        return []
    except Exception as e:
        print(f"[AVAILABILITY] Error getting slots: {e}")
        return AVAILABLE_SLOTS.get(day_name, [])


def save_availability(
    setting_type,
    day_of_week=None,
    specific_date=None,
    time_slots=None,
    apply_to_all=False,
):
    """Save availability settings"""
    try:
        conn = get_db()
        c = conn.cursor()

        if setting_type == "daily":
            if apply_to_all:
                # Apply same slots to all days of the week
                days = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
                for day in days:
                    c.execute(
                        "SELECT id FROM availability WHERE setting_type = 'daily' AND day_of_week = %s",
                        (day,),
                    )
                    if c.fetchone():
                        c.execute(
                            """
                            UPDATE availability SET time_slots = %s, updated_at = NOW()
                            WHERE setting_type = 'daily' AND day_of_week = %s
                        """,
                            (json.dumps(time_slots), day),
                        )
                    else:
                        c.execute(
                            """
                            INSERT INTO availability (setting_type, day_of_week, time_slots, is_active)
                            VALUES (%s, %s, %s, TRUE)
                        """,
                            (setting_type, day, json.dumps(time_slots)),
                        )
            elif specific_date:
                # Save for specific date
                c.execute(
                    "SELECT id FROM availability WHERE setting_type = 'daily' AND specific_date = %s",
                    (specific_date,),
                )
                if c.fetchone():
                    c.execute(
                        """
                        UPDATE availability SET time_slots = %s, updated_at = NOW()
                        WHERE setting_type = 'daily' AND specific_date = %s
                    """,
                        (json.dumps(time_slots), specific_date),
                    )
                else:
                    c.execute(
                        """
                        INSERT INTO availability (setting_type, specific_date, time_slots, is_active, updated_at)
                        VALUES (%s, %s, %s, TRUE, NOW())
                    """,
                        (setting_type, specific_date, json.dumps(time_slots)),
                    )
            elif day_of_week:
                # Update or insert specific day
                c.execute(
                    "SELECT id FROM availability WHERE setting_type = 'daily' AND day_of_week = %s",
                    (day_of_week,),
                )
                if c.fetchone():
                    c.execute(
                        """
                        UPDATE availability SET time_slots = %s, updated_at = NOW()
                        WHERE setting_type = 'daily' AND day_of_week = %s
                    """,
                        (json.dumps(time_slots), day_of_week),
                    )
                else:
                    c.execute(
                        """
                        INSERT INTO availability (setting_type, day_of_week, time_slots, is_active)
                        VALUES (%s, %s, %s, TRUE)
                    """,
                        (setting_type, day_of_week, json.dumps(time_slots)),
                    )

        elif setting_type == "weekly":
            if specific_date:
                # Save for specific week (specific_date = week start date)
                c.execute(
                    "SELECT id FROM availability WHERE setting_type = 'weekly' AND specific_date = %s",
                    (specific_date,),
                )
                if c.fetchone():
                    c.execute(
                        """
                        UPDATE availability SET time_slots = %s, updated_at = NOW()
                        WHERE setting_type = 'weekly' AND specific_date = %s
                    """,
                        (json.dumps(time_slots), specific_date),
                    )
                else:
                    c.execute(
                        """
                        INSERT INTO availability (setting_type, specific_date, time_slots, is_active, updated_at)
                        VALUES (%s, %s, %s, TRUE, NOW())
                    """,
                        (setting_type, specific_date, json.dumps(time_slots)),
                    )
            else:
                # Check if generic weekly entry exists
                c.execute(
                    "SELECT id FROM availability WHERE setting_type = 'weekly' AND specific_date IS NULL AND day_of_week IS NULL LIMIT 1"
                )
                if c.fetchone():
                    c.execute(
                        """
                        UPDATE availability SET time_slots = %s, updated_at = NOW()
                        WHERE setting_type = 'weekly' AND specific_date IS NULL
                    """,
                        (json.dumps(time_slots),),
                    )
                else:
                    c.execute(
                        """
                        INSERT INTO availability (setting_type, time_slots, updated_at)
                        VALUES (%s, %s, NOW())
                    """,
                        (setting_type, json.dumps(time_slots)),
                    )

        elif setting_type == "monthly":
            # Check if date entry exists
            c.execute(
                "SELECT id FROM availability WHERE setting_type = 'monthly' AND specific_date = %s",
                (specific_date,),
            )
            if c.fetchone():
                c.execute(
                    """
                    UPDATE availability SET time_slots = %s, updated_at = NOW()
                    WHERE setting_type = 'monthly' AND specific_date = %s
                """,
                    (json.dumps(time_slots), specific_date),
                )
            else:
                c.execute(
                    """
                    INSERT INTO availability (setting_type, specific_date, time_slots, updated_at)
                    VALUES (%s, %s, %s, NOW())
                """,
                    (setting_type, specific_date, json.dumps(time_slots)),
                )

        conn.commit()
        c.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving availability: {e}")
        return False


def get_all_availability():
    """Get all availability settings"""
    try:
        conn = get_db()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("SELECT * FROM availability ORDER BY day_of_week, specific_date")
        rows = c.fetchall()
        c.close()
        conn.close()
        return [dict(row) for row in rows]
    except:
        return []


def save_setting(setting_key, setting_value):
    """Save a setting"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO settings (setting_key, setting_value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (setting_key) DO UPDATE SET setting_value = %s, updated_at = NOW()
        """,
            (setting_key, setting_value, setting_value),
        )
        conn.commit()
        c.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving setting: {e}")
        return False


def get_api_key():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise Exception("GROQ_API_KEY not set in environment variables")
    return api_key


# Meeting functions using PostgreSQL
def save_meeting(name, email, date, time, topic):
    now = datetime.now()
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO meetings (name, email, date, time, topic, status) VALUES (%s, %s, %s, %s, %s, %s)",
        (name, email, date, time, topic, "scheduled"),
    )
    conn.commit()
    c.close()
    conn.close()


def get_meetings():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute(
        "SELECT name, email, date, time, topic, status FROM meetings ORDER BY id DESC"
    )
    rows = c.fetchall()
    c.close()
    conn.close()
    return [dict(row) for row in rows]


# Contact functions using PostgreSQL
def save_contact(name, email, message):
    now = datetime.now()
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO contacts (name, email, message, date, time) VALUES (%s, %s, %s, %s, %s)",
        (name, email, message, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")),
    )
    conn.commit()
    c.close()
    conn.close()


def get_contacts():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT name, email, message, date, time FROM contacts ORDER BY id DESC")
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
@app.route("/api/slots", methods=["GET"])
def get_slots():
    print(f"[SLOTS] Request received, DATABASE_AVAILABLE={DATABASE_AVAILABLE}")

    if not DATABASE_AVAILABLE:
        print("[SLOTS] Database not available")
        return jsonify(
            {
                "error": "Database not available",
                "available": [],
                "booked": [],
                "owner_timezone": "Asia/Karachi",
            }
        ), 200

    date = request.args.get("date")
    if not date:
        print("[SLOTS] No date provided")
        return jsonify({"error": "Date required"}), 400

    print(f"[SLOTS] Getting slots for date: {date}")

    booked = []
    try:
        meetings = get_meetings()
        booked = [
            m["time"]
            for m in meetings
            if m["date"] == date and m["status"] == "scheduled"
        ]
        print(f"[SLOTS] Booked slots: {booked}")
    except Exception as e:
        print(f"[SLOTS] Error getting booked slots: {e}")

    try:
        available = get_available_slots(date)
        print(f"[SLOTS] Available slots from DB: {available}")
        available = [s for s in available if s not in booked]
        print(f"[SLOTS] Final available slots: {available}")
    except Exception as e:
        print(f"[SLOTS] Error getting available slots: {e}")
        available = []

    try:
        owner_tz = get_owner_timezone()
        print(f"[SLOTS] Owner timezone: {owner_tz}")
    except Exception as e:
        print(f"[SLOTS] Error getting timezone: {e}")
        owner_tz = "Asia/Karachi"

    return jsonify(
        {
            "date": date,
            "available": available,
            "booked": booked,
            "owner_timezone": owner_tz,
        }
    )


@app.route("/api/health")
def health_check():
    """Health check endpoint to verify database and API status"""
    return jsonify(
        {
            "status": "ok",
            "database": {
                "configured": is_valid_db,
                "available": DATABASE_AVAILABLE,
                "message": DB_INIT_MESSAGE,
            },
            "api": {
                "chatbot": bool(os.environ.get("GROQ_API_KEY", "")),
                "telegram": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
            },
        }
    )


@app.route("/api/availability")
def get_availability():
    """Get availability for a specific mode and date"""
    if not DATABASE_AVAILABLE:
        return jsonify({"slots": []})

    mode = request.args.get("mode", "daily")
    date = request.args.get("date")

    if not date:
        return jsonify({"slots": []})

    try:
        conn = get_db()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if mode == "daily":
            # Try specific date first, then day of week
            c.execute(
                """
                SELECT time_slots FROM availability 
                WHERE setting_type = 'daily' AND specific_date = %s AND is_active = TRUE
            """,
                (date,),
            )
            result = c.fetchone()

            if not result:
                # Fall back to day of week
                day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
                c.execute(
                    """
                    SELECT time_slots FROM availability 
                    WHERE setting_type = 'daily' AND day_of_week = %s AND is_active = TRUE
                """,
                    (day_name,),
                )
                result = c.fetchone()

        elif mode == "weekly":
            # Get week start (Monday)
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            week_start = date_obj - timedelta(days=date_obj.weekday())
            week_start_str = week_start.strftime("%Y-%m-%d")

            # Try specific week first
            c.execute(
                """
                SELECT time_slots FROM availability 
                WHERE setting_type = 'weekly' AND specific_date = %s AND is_active = TRUE
            """,
                (week_start_str,),
            )
            result = c.fetchone()

            if not result:
                # Fall back to generic weekly
                c.execute("""
                    SELECT time_slots FROM availability 
                    WHERE setting_type = 'weekly' AND specific_date IS NULL AND is_active = TRUE LIMIT 1
                """)
                result = c.fetchone()

        elif mode == "monthly":
            c.execute(
                """
                SELECT time_slots FROM availability 
                WHERE setting_type = 'monthly' AND specific_date = %s AND is_active = TRUE
            """,
                (date,),
            )
            result = c.fetchone()

        c.close()
        conn.close()

        if result:
            return jsonify({"slots": json.loads(result["time_slots"])})

        return jsonify({"slots": []})
    except Exception as e:
        print(f"[AVAILABILITY API] Error: {e}")
        return jsonify({"slots": []})


@app.route("/api/debug/availability")
def debug_availability():
    """Debug endpoint to see what's stored in availability table"""
    if not DATABASE_AVAILABLE:
        return jsonify({"error": "Database not available"})

    try:
        conn = get_db()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get all availability data
        c.execute(
            "SELECT setting_type, day_of_week, specific_date, time_slots, is_active FROM availability ORDER BY setting_type, day_of_week, specific_date"
        )
        rows = c.fetchall()

        # Get current mode
        c.execute(
            "SELECT setting_value FROM settings WHERE setting_key = 'availability_mode'"
        )
        mode_row = c.fetchone()
        current_mode = mode_row[0] if mode_row else "daily"

        c.close()
        conn.close()

        return jsonify(
            {"current_mode": current_mode, "availability": [dict(row) for row in rows]}
        )
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/availability/markers")
def get_availability_markers():
    """Get availability markers for a month (for calendar visual indicators)"""
    if not DATABASE_AVAILABLE:
        return jsonify({"markers": {}})

    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    mode = request.args.get("mode", "daily")

    if not year or not month:
        return jsonify({"markers": {}})

    try:
        conn = get_db()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        markers = {}

        if mode == "daily":
            # Get specific dates that have custom availability
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"

            c.execute(
                """
                SELECT specific_date, time_slots FROM availability 
                WHERE setting_type = 'daily' 
                AND specific_date >= %s 
                AND specific_date < %s
                AND is_active = TRUE
            """,
                (start_date, end_date),
            )

            for row in c.fetchall():
                date_str = str(row["specific_date"])
                slots = json.loads(row["time_slots"])
                markers[date_str] = {"count": len(slots), "slots": slots}

            # Also get day-of-week availability
            c.execute("""
                SELECT day_of_week, time_slots FROM availability 
                WHERE setting_type = 'daily' 
                AND day_of_week IS NOT NULL
                AND is_active = TRUE
            """)
            day_slots = {}
            for row in c.fetchall():
                day_slots[row["day_of_week"]] = len(json.loads(row["time_slots"]))

        elif mode == "weekly":
            # Get week-specific availability
            c.execute("""
                SELECT specific_date, time_slots FROM availability 
                WHERE setting_type = 'weekly' 
                AND specific_date IS NOT NULL
                AND is_active = TRUE
            """)
            for row in c.fetchall():
                if row["specific_date"]:
                    date_str = str(row["specific_date"])
                    slots = json.loads(row["time_slots"])
                    markers[date_str] = {"count": len(slots), "slots": slots}

        elif mode == "monthly":
            # Get month-specific availability
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"

            c.execute(
                """
                SELECT specific_date, time_slots FROM availability 
                WHERE setting_type = 'monthly' 
                AND specific_date >= %s 
                AND specific_date < %s
                AND is_active = TRUE
            """,
                (start_date, end_date),
            )

            for row in c.fetchall():
                date_str = str(row["specific_date"])
                slots = json.loads(row["time_slots"])
                markers[date_str] = {"count": len(slots), "slots": slots}

        c.close()
        conn.close()

        return jsonify(
            {"markers": markers, "day_slots": day_slots if mode == "daily" else {}}
        )
    except Exception as e:
        print(f"[MARKERS] Error: {e}")
        return jsonify({"markers": {}, "day_slots": {}})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """Get or save settings"""
    if not DATABASE_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503

    if request.method == "GET":
        try:
            conn = get_db()
            c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            c.execute("SELECT * FROM settings")
            rows = c.fetchall()
            c.close()
            conn.close()
            settings = {row["setting_key"]: row["setting_value"] for row in rows}

            # Also get availability
            availability = get_all_availability()

            return jsonify({"settings": settings, "availability": availability})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # POST - Save settings
    try:
        data = request.get_json()

        if "owner_timezone" in data:
            save_setting("owner_timezone", data["owner_timezone"])

        if "availability_mode" in data:
            save_setting("availability_mode", data["availability_mode"])

        if "availability" in data:
            for av in data["availability"]:
                save_availability(
                    setting_type=av.get("setting_type", "daily"),
                    day_of_week=av.get("day_of_week"),
                    specific_date=av.get("specific_date"),
                    time_slots=av.get("time_slots", []),
                    apply_to_all=av.get("apply_to_all", False),
                )

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/book", methods=["POST"])
def book_meeting():
    if not DATABASE_AVAILABLE:
        return jsonify(
            {
                "success": False,
                "error": "Booking system temporarily unavailable. Database not connected.",
            }
        ), 503

    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        date = data.get("date", "").strip()
        time = data.get("time", "").strip()
        topic = data.get("topic", "").strip()

        if not all([name, email, date, time]):
            return jsonify({"success": False, "error": "All fields required"}), 400

        # Check if slot is already booked
        meetings = get_meetings()
        for m in meetings:
            if m["date"] == date and m["time"] == time and m["status"] == "scheduled":
                return jsonify({"success": False, "error": "Slot already booked"}), 400

        save_meeting(name, email, date, time, topic or "General Discussion")

        # Send Telegram notification
        telegram_msg = f"📅 <b>New Meeting Booked!</b>\n\n👤 <b>Name:</b> {name}\n📧 <b>Email:</b> {email}\n📆 <b>Date:</b> {date}\n⏰ <b>Time:</b> {time}\n💼 <b>Topic:</b> {topic or 'General Discussion'}"
        send_telegram_message(telegram_msg)

        return jsonify({"success": True})
    except Exception as e:
        print(f"Booking error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/meetings")
def api_meetings():
    if not DATABASE_AVAILABLE:
        return jsonify([]), 200

    meetings = get_meetings()
    response = jsonify(meetings)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/api/chat", methods=["POST"])
def chat():
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405

    # Rate limiting
    client_ip = request.remote_addr or "unknown"
    allowed, remaining = check_rate_limit(client_ip)
    if not allowed:
        return jsonify(
            {"error": "Too many requests. Please wait a moment and try again."}
        ), 429

    try:
        data = request.get_json()
    except:
        return jsonify({"error": "Invalid JSON"}), 400

    if not data:
        return jsonify({"error": "Empty request"}), 400

    messages = data.get("messages", [])

    if not messages or not isinstance(messages, list):
        return jsonify({"error": "Invalid request"}), 400

    try:
        api_key = get_api_key()
        cleaned_messages = []
        for msg in messages[-6:]:
            role = msg.get("role", "user")
            content = clean_message(msg.get("content", ""))
            if content:
                cleaned_messages.append({"role": role, "content": content})

        formatted_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *cleaned_messages,
        ]

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": formatted_messages,
                "temperature": 0.7,
                "max_tokens": 350,
            },
            timeout=30,
        )

        print(f"Groq API response: {response.status_code}")

        if response.status_code != 200:
            print(f"Groq API error: {response.status_code} - {response.text}")
            return jsonify({"error": f"AI service error: {response.text[:100]}"}), 500

        result = response.json()

        if "choices" not in result or not result["choices"]:
            return jsonify({"error": "Invalid AI response"}), 500

        assistant_message = result["choices"][0]["message"]["content"]

        if not assistant_message:
            return jsonify({"error": "Empty AI response"}), 500

        return jsonify({"message": assistant_message})

    except requests.exceptions.Timeout:
        print("Request timeout")
        return jsonify({"error": "Request timed out. Please try again."}), 500
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": "Failed to process request"}), 500


@app.route("/api/contact", methods=["POST"])
def contact():
    if not DATABASE_AVAILABLE:
        return jsonify(
            {
                "success": False,
                "error": "Contact form temporarily unavailable. Database not connected.",
            }
        ), 503

    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        message = data.get("message", "").strip()

        # Validation
        if not name or not email or not message:
            return jsonify({"success": False, "error": "All fields are required"}), 400

        if len(name) > 100:
            return jsonify(
                {"success": False, "error": "Name must be under 100 characters"}
            ), 400

        if len(message) > 2000:
            return jsonify(
                {"success": False, "error": "Message must be under 2000 characters"}
            ), 400

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            return jsonify({"success": False, "error": "Invalid email format"}), 400

        save_contact(name, email, message)

        # Send Telegram notification
        telegram_msg = f"📬 <b>New Contact Message</b>\n\n👤 <b>Name:</b> {name}\n📧 <b>Email:</b> {email}\n💬 <b>Message:</b>\n{message}"
        send_telegram_message(telegram_msg)

        return jsonify({"success": True})
    except Exception as e:
        print(f"Contact error: {e}")
        return jsonify({"success": False, "error": "Failed to save message"}), 500


ADMIN_HTML = """
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

            <!-- Availability Settings -->
            <div class="contacts-section" style="margin-top: 40px;">
                <h2>⚙️ Availability Settings</h2>
                
                <!-- Mode Selection -->
                <div class="settings-card" style="background: var(--dark-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
                    <h3 style="font-size: 1rem; margin-bottom: 15px; color: var(--primary);">Availability Mode</h3>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="mode-btn active" data-mode="daily" onclick="setAvailabilityMode('daily')" style="padding: 10px 20px; background: rgba(0,240,255,0.1); border: 1px solid var(--primary); border-radius: 8px; color: var(--primary); cursor: pointer;">📅 Daily</button>
                        <button class="mode-btn" data-mode="weekly" onclick="setAvailabilityMode('weekly')" style="padding: 10px 20px; background: transparent; border: 1px solid var(--border); border-radius: 8px; color: var(--text-muted); cursor: pointer;">📆 Weekly</button>
                        <button class="mode-btn" data-mode="monthly" onclick="setAvailabilityMode('monthly')" style="padding: 10px 20px; background: transparent; border: 1px solid var(--border); border-radius: 8px; color: var(--text-muted); cursor: pointer;">📆 Monthly</button>
                    </div>
                </div>

                <!-- Timezone Setting -->
                <div class="settings-card" style="background: var(--dark-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
                    <h3 style="font-size: 1rem; margin-bottom: 15px; color: var(--primary);">🌍 Your Timezone</h3>
                    <select id="ownerTimezone" onchange="saveTimezone(this.value)" style="width: 100%; padding: 12px 16px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 10px; color: var(--text); font-family: 'Outfit', sans-serif; font-size: 1rem;">
                        <option value="Asia/Karachi">🇵🇰 Pakistan (PKT) - UTC+5</option>
                        <option value="America/New_York">🇺🇸 New York (EST) - UTC-5</option>
                        <option value="America/Los_Angeles">🇺🇸 Los Angeles (PST) - UTC-8</option>
                        <option value="Europe/London">🇬🇧 London (GMT) - UTC+0</option>
                        <option value="Europe/Paris">🇪🇺 Paris (CET) - UTC+1</option>
                        <option value="Asia/Dubai">🇦🇪 Dubai (GST) - UTC+4</option>
                        <option value="Asia/Kolkata">🇮🇳 India (IST) - UTC+5:30</option>
                        <option value="Asia/Singapore">🇸🇬 Singapore (SGT) - UTC+8</option>
                        <option value="Asia/Tokyo">🇯🇵 Tokyo (JST) - UTC+9</option>
                        <option value="Australia/Sydney">🇦🇺 Sydney (AEDT) - UTC+11</option>
                    </select>
                </div>

                <!-- Daily Mode - Date Selector with Calendar -->
                <div id="dailyModePanel" class="settings-card" style="background: var(--dark-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
                    <h3 style="font-size: 1rem; margin-bottom: 15px; color: var(--primary);">🕐 Daily Availability</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 15px;">Select a specific date and set its time slots:</p>
                    
                    <!-- Month Navigator -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <button onclick="changeDailyMonth(-1)" style="padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 8px; color: var(--text); cursor: pointer;">◀</button>
                        <span id="dailyMonthYear" style="font-size: 1rem; font-weight: 600; color: var(--text);"></span>
                        <button onclick="changeDailyMonth(1)" style="padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 8px; color: var(--text); cursor: pointer;">▶</button>
                    </div>
                    
                    <!-- Calendar Grid -->
                    <div id="dailyCalendarGrid" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-bottom: 20px;">
                    </div>
                    
                    <!-- Selected Date Display -->
                    <div style="margin-bottom: 15px; padding: 10px; background: rgba(0,240,255,0.1); border-radius: 8px;">
                        <span style="color: var(--primary);">Selected: </span>
                        <span id="selectedDailyDate" style="color: var(--text); font-weight: 600;">Click a date above</span>
                    </div>
                    
                    <!-- Quick Presets -->
                    <div style="margin-bottom: 15px;">
                        <span style="color: var(--text-muted); font-size: 0.85rem; margin-right: 10px;">Quick Presets:</span>
                        <button onclick="applyPreset('morning')" style="padding: 6px 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 0.8rem; cursor: pointer; margin-right: 5px;">🌅 Morning</button>
                        <button onclick="applyPreset('afternoon')" style="padding: 6px 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 0.8rem; cursor: pointer; margin-right: 5px;">🌆 Afternoon</button>
                        <button onclick="applyPreset('evening')" style="padding: 6px 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 0.8rem; cursor: pointer; margin-right: 5px;">🌙 Evening</button>
                        <button onclick="applyPreset('night')" style="padding: 6px 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 0.8rem; cursor: pointer; margin-right: 5px;">🌌 Night</button>
                        <button onclick="applyPreset('allday')" style="padding: 6px 12px; background: rgba(0,240,255,0.1); border: 1px solid var(--primary); border-radius: 6px; color: var(--primary); font-size: 0.8rem; cursor: pointer;">📅 All Day</button>
                    </div>
                    
                    <!-- Time Slots with AM/PM -->
                    <div id="dailyTimeSlotsContainer" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 10px;">
                    </div>
                    
                    <!-- Save Button -->
                    <button onclick="saveDailyByDate()" style="margin-top: 20px; padding: 12px 24px; background: linear-gradient(135deg, var(--primary), var(--secondary)); border: none; border-radius: 10px; color: var(--dark); font-weight: 600; cursor: pointer;">💾 Save for Selected Date</button>
                    <p id="saveStatus" style="margin-top: 10px; color: var(--primary); display: none;">✓ Saved successfully!</p>
                </div>

                <!-- Weekly Mode -->
                <div id="weeklyModePanel" class="settings-card" style="display:none; background: var(--dark-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
                    <h3 style="font-size: 1rem; margin-bottom: 15px; color: var(--primary);">🕐 Weekly Availability</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 15px;">Select a week and set time slots that apply to all 7 days:</p>
                    
                    <!-- Week Navigator -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <button onclick="changeWeeklyWeek(-1)" style="padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 8px; color: var(--text); cursor: pointer;">◀</button>
                        <span id="weeklyWeekRange" style="font-size: 1rem; font-weight: 600; color: var(--text);"></span>
                        <button onclick="changeWeeklyWeek(1)" style="padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 8px; color: var(--text); cursor: pointer;">▶</button>
                    </div>
                    
                    <!-- Week Days Preview -->
                    <div id="weeklyDaysPreview" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-bottom: 20px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 8px;">
                    </div>
                    
                    <!-- Selected Week Display -->
                    <div style="margin-bottom: 15px; padding: 10px; background: rgba(0,240,255,0.1); border-radius: 8px;">
                        <span style="color: var(--primary);">Selected Week: </span>
                        <span id="selectedWeeklyWeek" style="color: var(--text); font-weight: 600;"></span>
                    </div>
                    
                    <!-- Time Slots with AM/PM -->
                    <div id="weeklyTimeSlotsContainer" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 10px;">
                    </div>
                    
                    <!-- Save Button -->
                    <button onclick="saveWeeklyForWeek()" style="margin-top: 20px; padding: 12px 24px; background: linear-gradient(135deg, var(--primary), var(--secondary)); border: none; border-radius: 10px; color: var(--dark); font-weight: 600; cursor: pointer;">💾 Save for This Week</button>
                    <p id="weeklySaveStatus" style="margin-top: 10px; color: var(--primary); display: none;">✓ Saved successfully!</p>
                </div>

                <!-- Monthly Mode -->
                <div id="monthlyModePanel" class="settings-card" style="display:none; background: var(--dark-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
                    <h3 style="font-size: 1rem; margin-bottom: 15px; color: var(--primary);">🕐 Monthly Availability</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 15px;">Select a specific date in the month to set its time slots:</p>
                    
                    <!-- Month Navigator -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <button onclick="changeMonthlyMonth(-1)" style="padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 8px; color: var(--text); cursor: pointer;">◀</button>
                        <span id="monthlyMonthYear" style="font-size: 1rem; font-weight: 600; color: var(--text);"></span>
                        <button onclick="changeMonthlyMonth(1)" style="padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 8px; color: var(--text); cursor: pointer;">▶</button>
                    </div>
                    
                    <!-- Calendar Grid Header -->
                    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-bottom: 5px; text-align: center;">
                        <div style="color: var(--text-muted); font-size: 0.75rem;">Sun</div>
                        <div style="color: var(--text-muted); font-size: 0.75rem;">Mon</div>
                        <div style="color: var(--text-muted); font-size: 0.75rem;">Tue</div>
                        <div style="color: var(--text-muted); font-size: 0.75rem;">Wed</div>
                        <div style="color: var(--text-muted); font-size: 0.75rem;">Thu</div>
                        <div style="color: var(--text-muted); font-size: 0.75rem;">Fri</div>
                        <div style="color: var(--text-muted); font-size: 0.75rem;">Sat</div>
                    </div>
                    
                    <!-- Calendar Grid -->
                    <div id="monthlyCalendarGrid" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-bottom: 20px;">
                    </div>
                    
                    <!-- Selected Date Display -->
                    <div style="margin-bottom: 15px; padding: 10px; background: rgba(0,240,255,0.1); border-radius: 8px;">
                        <span style="color: var(--primary);">Selected: </span>
                        <span id="selectedMonthlyDate" style="color: var(--text); font-weight: 600;">Click a date above</span>
                    </div>
                    
                    <!-- Time Slots with AM/PM -->
                    <div id="monthlyTimeSlotsContainer" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 10px;">
                    </div>
                    
                    <!-- Save Button -->
                    <button onclick="saveMonthlyForDate()" style="margin-top: 20px; padding: 12px 24px; background: linear-gradient(135deg, var(--primary), var(--secondary)); border: none; border-radius: 10px; color: var(--dark); font-weight: 600; cursor: pointer;">💾 Save for Selected Date</button>
                    <p id="monthlySaveStatus" style="margin-top: 10px; color: var(--primary); display: none;">✓ Saved successfully!</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Time slots in 24hr format for backend
        const timeSlots24hr = ["23:00", "00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"];
        
        // Convert 24hr to 12hr AM/PM
        function convertTo12Hour(time24) {
            const [hours, minutes] = time24.split(':');
            let h = parseInt(hours);
            const m = minutes;
            const period = h >= 12 ? 'PM' : 'AM';
            if (h === 0) h = 12;
            else if (h > 12) h -= 12;
            return `${h}:${m} ${period}`;
        }
        
        // Convert 12hr to 24hr
        function convertTo24Hour(time12) {
            const match = time12.match(/(\d+):(\d+)\s+(AM|PM)/i);
            if (!match) return time12;
            let hours = parseInt(match[1]);
            const minutes = match[2];
            const period = match[3].toUpperCase();
            if (period === 'PM' && hours !== 12) hours += 12;
            if (period === 'AM' && hours === 12) hours = 0;
            return `${hours.toString().padStart(2, '0')}:${minutes}`;
        }
        
        let currentMode = 'daily';
        let dayAvailability = {}; // Store availability for each day
        let weeklySlots = [];
        let monthlySlots = [];
        
        // Calendar state variables
        let dailyCurrentDate = new Date();
        let weeklyCurrentWeekStart = getWeekStart(new Date());
        let monthlyCurrentDate = new Date();
        let selectedDailyDate = null;
        let selectedWeeklyWeekStart = null;
        let selectedMonthlyDate = null;
        
        // Helper to get week start (Monday)
        function getWeekStart(date) {
            const d = new Date(date);
            const day = d.getDay();
            const diff = d.getDate() - day + (day === 0 ? -6 : 1);
            return new Date(d.setDate(diff));
        }
        
        // Format date as YYYY-MM-DD (local time, not UTC)
        function formatDate(date) {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }
        
        // Format date for display
        function formatDisplayDate(date) {
            return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
        }
        
        // Get month name and year
        function getMonthYear(date) {
            return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        }
        
        // Daily Mode Functions
        function changeDailyMonth(delta) {
            dailyCurrentDate.setMonth(dailyCurrentDate.getMonth() + delta);
            renderDailyCalendar();
        }
        
        let dailyMarkers = {};
        
        function renderDailyCalendar() {
            const year = dailyCurrentDate.getFullYear();
            const month = dailyCurrentDate.getMonth();
            
            document.getElementById('dailyMonthYear').textContent = getMonthYear(dailyCurrentDate);
            
            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const startDay = firstDay.getDay();
            const daysInMonth = lastDay.getDate();
            
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            // Fetch availability markers for this month
            fetch(`/api/availability/markers?year=${year}&month=${month+1}&mode=daily`)
                .then(res => res.json())
                .then(data => {
                    dailyMarkers = data.markers || {};
                    renderCalendarGrid();
                })
                .catch(err => {
                    console.error('Error loading markers:', err);
                    renderCalendarGrid();
                });
            
            function renderCalendarGrid() {
                let html = '';
                
                // Day headers
                const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                dayNames.forEach(day => {
                    html += `<div style="text-align: center; padding: 5px; color: var(--text-muted); font-size: 0.7rem;">${day}</div>`;
                });
                
                // Empty cells before first day
                for (let i = 0; i < startDay; i++) {
                    html += '<div></div>';
                }
                
                // Days of month
                for (let day = 1; day <= daysInMonth; day++) {
                    const date = new Date(year, month, day);
                    const dateStr = formatDate(date);
                    const isSelected = selectedDailyDate === dateStr;
                    const isPast = date < today;
                    const isToday = date.getTime() === today.getTime();
                    const marker = dailyMarkers[dateStr];
                    const hasSlots = marker && marker.count > 0;
                    
                    const markerDot = hasSlots 
                        ? `<div style="width: 6px; height: 6px; background: ${marker.count >= 5 ? 'var(--primary)' : marker.count >= 3 ? 'var(--secondary)' : '#00ff88'}; border-radius: 50%; margin: 4px auto 0;"></div>` 
                        : '';
                
                    html += `<div onclick="selectDailyDate('${dateStr}')" 
                        style="text-align: center; padding: 8px; 
                        background: ${isSelected ? 'rgba(0,240,255,0.2)' : isToday ? 'rgba(255,0,255,0.1)' : hasSlots ? 'rgba(0,255,136,0.1)' : 'rgba(255,255,255,0.03)'};
                        border: 1px solid ${isSelected ? 'var(--primary)' : isToday ? 'var(--secondary)' : hasSlots ? '#00ff88' : 'var(--border)'};
                        border-radius: 8px; cursor: ${isPast ? 'not-allowed' : 'pointer'};
                        color: ${isPast ? 'var(--text-muted)' : isSelected ? 'var(--primary)' : 'var(--text)'};
                        opacity: ${isPast ? 0.5 : 1};
                        font-weight: ${isToday ? '600' : '400'};">
                        <div>${day}</div>
                        ${markerDot}
                    </div>`;
                }
                
                document.getElementById('dailyCalendarGrid').innerHTML = html;
            }
        }
        
        function selectDailyDate(dateStr) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const selected = new Date(dateStr);
            
            if (selected < today) return; // Can't select past dates
            
            selectedDailyDate = dateStr;
            document.getElementById('selectedDailyDate').textContent = formatDisplayDate(selected);
            
            // Load existing slots for this date from server
            loadSlotsForDate('daily', dateStr);
        }
        
        function loadSlotsForDate(mode, dateStr) {
            fetch(`/api/availability?mode=${mode}&date=${dateStr}`)
                .then(res => res.json())
                .then(data => {
                    const slots = data.slots || [];
                    renderTimeSlots('dailyTimeSlotsContainer', slots);
                })
                .catch(err => {
                    console.error('Error loading slots:', err);
                    renderTimeSlots('dailyTimeSlotsContainer', []);
                });
        }
        
        async function saveDailyByDate() {
            if (!selectedDailyDate) {
                alert('Please select a date first');
                return;
            }
            
            const selectedSlots = Array.from(document.querySelectorAll('#dailyTimeSlotsContainer .time-slot-checkbox:checked')).map(cb => cb.value);
            
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        availability_mode: 'daily',
                        availability: [{
                            setting_type: 'daily',
                            specific_date: selectedDailyDate,
                            time_slots: selectedSlots
                        }]
                    })
                });
                document.getElementById('saveStatus').style.display = 'block';
                setTimeout(() => {
                    document.getElementById('saveStatus').style.display = 'none';
                }, 3000);
            } catch (e) {
                console.error('Error saving daily availability:', e);
            }
        }
        
        // Weekly Mode Functions
        function changeWeeklyWeek(delta) {
            weeklyCurrentWeekStart.setDate(weeklyCurrentWeekStart.getDate() + (delta * 7));
            renderWeeklyCalendar();
        }
        
        function renderWeeklyCalendar() {
            const weekEnd = new Date(weeklyCurrentWeekStart);
            weekEnd.setDate(weekEnd.getDate() + 6);
            
            document.getElementById('weeklyWeekRange').textContent = 
                `${formatDisplayDate(weeklyCurrentWeekStart)} - ${formatDisplayDate(weekEnd)}`;
            
            selectedWeeklyWeekStart = formatDate(weeklyCurrentWeekStart);
            document.getElementById('selectedWeeklyWeek').textContent = 
                `${formatDisplayDate(weeklyCurrentWeekStart)} - ${formatDisplayDate(weekEnd)}`;
            
            // Render days preview
            let daysHtml = '';
            const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            
            for (let i = 0; i < 7; i++) {
                const d = new Date(weeklyCurrentWeekStart);
                d.setDate(d.getDate() + i);
                daysHtml += `<div style="text-align: center; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 6px;">
                    <div style="color: var(--text-muted); font-size: 0.7rem;">${dayNames[i]}</div>
                    <div style="color: var(--text); font-weight: 600;">${d.getDate()}</div>
                </div>`;
            }
            
            document.getElementById('weeklyDaysPreview').innerHTML = daysHtml;
            
            // Load existing slots for this week from server
            fetch(`/api/availability?mode=weekly&date=${selectedWeeklyWeekStart}`)
                .then(res => res.json())
                .then(data => {
                    const slots = data.slots || [];
                    renderTimeSlots('weeklyTimeSlotsContainer', slots);
                })
                .catch(err => {
                    console.error('Error loading weekly slots:', err);
                    renderTimeSlots('weeklyTimeSlotsContainer', []);
                });
        }
        
        async function saveWeeklyForWeek() {
            if (!selectedWeeklyWeekStart) {
                alert('Please select a week first');
                return;
            }
            
            const selectedSlots = Array.from(document.querySelectorAll('#weeklyTimeSlotsContainer .time-slot-checkbox:checked')).map(cb => cb.value);
            
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        availability_mode: 'weekly',
                        availability: [{
                            setting_type: 'weekly',
                            specific_date: selectedWeeklyWeekStart,
                            time_slots: selectedSlots
                        }]
                    })
                });
                document.getElementById('weeklySaveStatus').style.display = 'block';
                setTimeout(() => {
                    document.getElementById('weeklySaveStatus').style.display = 'none';
                }, 3000);
            } catch (e) {
                console.error('Error saving weekly availability:', e);
            }
        }
        
        // Monthly Mode Functions
        function changeMonthlyMonth(delta) {
            monthlyCurrentDate.setMonth(monthlyCurrentDate.getMonth() + delta);
            renderMonthlyCalendar();
        }
        
        function renderMonthlyCalendar() {
            const year = monthlyCurrentDate.getFullYear();
            const month = monthlyCurrentDate.getMonth();
            
            document.getElementById('monthlyMonthYear').textContent = getMonthYear(monthlyCurrentDate);
            
            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const startDay = firstDay.getDay();
            const daysInMonth = lastDay.getDate();
            
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            let html = '';
            
            // Empty cells before first day
            for (let i = 0; i < startDay; i++) {
                html += '<div></div>';
            }
            
            // Days of month
            for (let day = 1; day <= daysInMonth; day++) {
                const date = new Date(year, month, day);
                const dateStr = formatDate(date);
                const isSelected = selectedMonthlyDate === dateStr;
                const isPast = date < today;
                const isToday = date.getTime() === today.getTime();
                
                html += `<div onclick="selectMonthlyDate('${dateStr}')" 
                    style="text-align: center; padding: 10px; 
                    background: ${isSelected ? 'rgba(0,240,255,0.2)' : isToday ? 'rgba(255,0,255,0.1)' : 'rgba(255,255,255,0.03)'};
                    border: 1px solid ${isSelected ? 'var(--primary)' : isToday ? 'var(--secondary)' : 'var(--border)'};
                    border-radius: 8px; cursor: ${isPast ? 'not-allowed' : 'pointer'};
                    color: ${isPast ? 'var(--text-muted)' : isSelected ? 'var(--primary)' : 'var(--text)'};
                    opacity: ${isPast ? 0.5 : 1};
                    font-weight: ${isToday ? '600' : '400'};">${day}</div>`;
            }
            
            document.getElementById('monthlyCalendarGrid').innerHTML = html;
        }
        
        function selectMonthlyDate(dateStr) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const selected = new Date(dateStr);
            
            if (selected < today) return; // Can't select past dates
            
            selectedMonthlyDate = dateStr;
            document.getElementById('selectedMonthlyDate').textContent = formatDisplayDate(selected);
            
            // Load existing slots for this date from server
            fetch(`/api/availability?mode=monthly&date=${dateStr}`)
                .then(res => res.json())
                .then(data => {
                    const slots = data.slots || [];
                    renderTimeSlots('monthlyTimeSlotsContainer', slots);
                })
                .catch(err => {
                    console.error('Error loading slots:', err);
                    renderTimeSlots('monthlyTimeSlotsContainer', []);
                });
        }
        
        async function saveMonthlyForDate() {
            if (!selectedMonthlyDate) {
                alert('Please select a date first');
                return;
            }
            
            const selectedSlots = Array.from(document.querySelectorAll('#monthlyTimeSlotsContainer .time-slot-checkbox:checked')).map(cb => cb.value);
            
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        availability_mode: 'monthly',
                        availability: [{
                            setting_type: 'monthly',
                            specific_date: selectedMonthlyDate,
                            time_slots: selectedSlots
                        }]
                    })
                });
                document.getElementById('monthlySaveStatus').style.display = 'block';
                setTimeout(() => {
                    document.getElementById('monthlySaveStatus').style.display = 'none';
                }, 3000);
            } catch (e) {
                console.error('Error saving monthly availability:', e);
            }
        }
        
        // Initialize calendars on load
        function initCalendars() {
            renderDailyCalendar();
            renderWeeklyCalendar();
            renderMonthlyCalendar();
        }
        
        function renderTimeSlots(containerId, selectedSlots) {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            container.innerHTML = timeSlots24hr.map(time => {
                const time12 = convertTo12Hour(time);
                const isSelected = selectedSlots.includes(time);
                return `
                    <label style="display: flex; align-items: center; gap: 8px; padding: 10px; background: ${isSelected ? 'rgba(0,240,255,0.15)' : 'rgba(255,255,255,0.03)'}; border: 1px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}; border-radius: 8px; cursor: pointer; transition: all 0.2s;">
                        <input type="checkbox" value="${time}" ${isSelected ? 'checked' : ''} class="time-slot-checkbox" style="width: 18px; height: 18px; accent-color: var(--primary);">
                        <span style="color: ${isSelected ? 'var(--primary)' : 'var(--text)'}; font-size: 0.85rem; font-weight: ${isSelected ? '600' : '400'}">${time12}</span>
                    </label>
                `;
            }).join('');
        }
        
        function applyPreset(preset) {
            let presetSlots = [];
            switch(preset) {
                case 'morning':
                    presetSlots = ['06:00', '07:00', '08:00', '09:00', '10:00', '11:00'];
                    break;
                case 'afternoon':
                    presetSlots = ['12:00', '13:00', '14:00', '15:00', '16:00', '17:00'];
                    break;
                case 'evening':
                    presetSlots = ['18:00', '19:00', '20:00', '21:00', '22:00', '23:00'];
                    break;
                case 'night':
                    presetSlots = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00'];
                    break;
                case 'allday':
                    presetSlots = [...timeSlots24hr];
                    break;
            }
            renderTimeSlots('dailyTimeSlotsContainer', presetSlots);
        }
        
        function loadSettings() {
            console.log("Loading settings...");
            fetch('/api/settings?_t=' + Date.now())
                .then(res => {
                    console.log("Settings response status:", res.status);
                    return res.json();
                })
                .then(data => {
                    console.log("Settings data:", data);
                    
                    // Check for error response
                    if (data.error) {
                        console.error("Error loading settings:", data.error);
                        document.getElementById('saveStatus').textContent = 'Error: ' + data.error;
                        document.getElementById('saveStatus').style.display = 'block';
                        return;
                    }
                    
                    if (data.settings) {
                        if (data.settings.owner_timezone) {
                            document.getElementById('ownerTimezone').value = data.settings.owner_timezone;
                        }
                        if (data.settings.availability_mode) {
                            currentMode = data.settings.availability_mode;
                            updateModeUI();
                        }
                    }
                    
                    // Load availability data - initialize with defaults if empty
                    if (data.availability && data.availability.length > 0) {
                        data.availability.forEach(av => {
                            try {
                                if (av.setting_type === 'daily' && av.day_of_week) {
                                    dayAvailability[av.day_of_week] = JSON.parse(av.time_slots || '[]');
                                } else if (av.setting_type === 'weekly') {
                                    weeklySlots = JSON.parse(av.time_slots || '[]');
                                } else if (av.setting_type === 'monthly') {
                                    monthlySlots = JSON.parse(av.time_slots || '[]');
                                }
                            } catch (e) {
                                console.error("Error parsing availability:", e);
                            }
                        });
                    } else {
                        // Initialize with default slots if no data
                        console.log("No availability data, using defaults");
                        const defaultSlots = ["23:00", "00:00", "01:00"];
                        weeklySlots = defaultSlots;
                        monthlySlots = defaultSlots;
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].forEach(day => {
                            dayAvailability[day] = defaultSlots;
                        });
                    }
                    
                    // Initialize UI
                    renderTimeSlots('weeklyTimeSlotsContainer', weeklySlots);
                    renderTimeSlots('monthlyTimeSlotsContainer', monthlySlots);
                    initCalendars();
                    console.log("Settings loaded successfully");
                })
                .catch(error => {
                    console.error("Error loading settings:", error);
                    document.getElementById('saveStatus').textContent = 'Error loading settings: ' + error.message;
                    document.getElementById('saveStatus').style.display = 'block';
                });
        }
        
        function updateModeUI() {
            document.querySelectorAll('.mode-btn').forEach(btn => {
                btn.classList.remove('active');
                btn.style.background = 'transparent';
                btn.style.borderColor = 'var(--border)';
                btn.style.color = 'var(--text-muted)';
                if (btn.dataset.mode === currentMode) {
                    btn.classList.add('active');
                    btn.style.background = 'rgba(0,240,255,0.1)';
                    btn.style.borderColor = 'var(--primary)';
                    btn.style.color = 'var(--primary)';
                }
            });
            
            document.getElementById('dailyModePanel').style.display = currentMode === 'daily' ? 'block' : 'none';
            document.getElementById('weeklyModePanel').style.display = currentMode === 'weekly' ? 'block' : 'none';
            document.getElementById('monthlyModePanel').style.display = currentMode === 'monthly' ? 'block' : 'none';
        }
        
        async function setAvailabilityMode(mode) {
            currentMode = mode;
            updateModeUI();
            
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ availability_mode: mode })
                });
            } catch (e) {
                console.error('Error saving mode:', e);
            }
        }
        
        function showSaveStatus() {
            const status = document.getElementById('saveStatus');
            status.style.display = 'block';
            status.textContent = '✓ Saved successfully!';
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
        }
        
        function checkAuth() {
            const isLoggedIn = sessionStorage.getItem('adminLoggedIn');
            if (isLoggedIn === 'true') {
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('dashboardSection').classList.add('active');
                loadContacts();
                loadMeetings();
                loadSettings();
                initCalendars();
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
"""


@app.route("/ahmadAdmin")
def admin():
    response = make_response(render_template_string(ADMIN_HTML))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    print("Login attempt received")
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            print("Login successful!")
            return jsonify({"success": True})
        print("Login failed - invalid credentials")
        return jsonify({"success": False}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/contacts")
@login_required
def admin_contacts():
    if not DATABASE_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503
    try:
        print(f"Loading contacts, session: {session.get('logged_in')}")
        contacts = get_contacts()
        print(f"Found {len(contacts)} contacts")
        response = jsonify(contacts)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        return response
    except Exception as e:
        print(f"Admin contacts error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/meetings")
@login_required
def admin_meetings():
    if not DATABASE_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503
    try:
        print(f"Loading meetings, session: {session.get('logged_in')}")
        meetings = get_meetings()
        print(f"Found {len(meetings)} meetings")
        response = jsonify(meetings)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        return response
    except Exception as e:
        print(f"Admin meetings error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/logout")
def admin_logout():
    session.pop("logged_in", None)
    return jsonify({"success": True})


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/chatbot")
def chatbot():
    return send_from_directory(".", "chatbot.html")


@app.route("/book")
def booking():
    return send_from_directory(".", "book.html")


@app.route("/JogiWorld")
def jogiworld():
    return send_from_directory(".", "jogiworld.html")


@app.route("/ahmadAI")
def ahmadai():
    return send_from_directory(".", "ahmadAI.html")


# ==========================================
# AHMADAI NEWS API (must be before catch-all)
# ==========================================

NEWS_DB_PATH = os.environ.get("NEWS_DB_PATH", "news.db")
NEON_DB_URL = os.environ.get("NEON_DB_URL", "")


def get_news_db():
    if NEON_DB_URL:
        import psycopg2

        conn = psycopg2.connect(NEON_DB_URL)
        conn.autocommit = True
        return conn

    import sqlite3

    conn = sqlite3.connect(NEWS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_news_db():
    if NEON_DB_URL:
        import psycopg2

        try:
            conn = psycopg2.connect(NEON_DB_URL)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS news_cache (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT,
                    source TEXT,
                    source_type TEXT,
                    url TEXT UNIQUE,
                    thumbnail TEXT,
                    category TEXT DEFAULT 'News',
                    trending_score INTEGER DEFAULT 0,
                    published_at TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_processed BOOLEAN DEFAULT FALSE
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS news_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            c.close()
            conn.close()
            print("✅ Neon news tables created")
        except Exception as e:
            print(f"❌ Neon init error: {e}")
        return

    import sqlite3

    conn = sqlite3.connect(NEWS_DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS news_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            source TEXT,
            source_type TEXT,
            url TEXT UNIQUE,
            thumbnail TEXT,
            category TEXT DEFAULT 'News',
            trending_score INTEGER DEFAULT 0,
            published_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_processed BOOLEAN DEFAULT FALSE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS news_metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@app.route("/api/news/debug")
def news_debug():
    import sqlite3

    try:
        init_news_db()
        conn = sqlite3.connect(NEWS_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        c.execute("SELECT COUNT(*) FROM news_cache")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM news_cache WHERE is_processed = TRUE")
        processed = c.fetchone()[0]
        conn.close()
        return jsonify(
            {
                "db_path": NEWS_DB_PATH,
                "tables": tables,
                "total_news": total,
                "processed_news": processed,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/news")
def get_news():
    try:
        init_news_db()
        conn = get_news_db()
        is_postgres = bool(NEON_DB_URL)

        category = request.args.get("category", "all")
        source_type = request.args.get("source", "all")
        limit = int(request.args.get("limit", 50))

        query = "SELECT id, title, summary, source, source_type, url, thumbnail, category, trending_score, published_at FROM news_cache WHERE is_processed = TRUE"
        params = []

        if category and category != "all":
            query += " AND category = %s"
            params.append(category)

        if source_type and source_type != "all":
            query += " AND source_type = %s"
            params.append(source_type)

        query += " ORDER BY trending_score DESC, created_at DESC LIMIT %s"
        params.append(limit)

        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()
        c.close()
        conn.close()

        news = []
        for row in rows:
            news.append(
                {
                    "id": row[0],
                    "title": row[1] or "",
                    "summary": row[2] or "",
                    "source": row[3] or "Unknown",
                    "source_type": row[4] or "blog",
                    "url": row[5] or "",
                    "thumbnail": row[6] or "",
                    "category": row[7] or "News",
                    "trending_score": row[8] or 0,
                    "published_at": row[9] or "",
                }
            )

        last_update = None
        try:
            conn2 = get_news_db()
            c2 = conn2.cursor()
            c2.execute("SELECT value FROM news_metadata WHERE key = 'last_update'")
            row = c2.fetchone()
            if row:
                last_update = row[0]
            c2.close()
            conn2.close()
        except:
            pass

        return jsonify({"news": news, "last_update": last_update, "count": len(news)})
    except Exception as e:
        print(f"News API error: {e}")
        return jsonify({"news": [], "error": str(e)})


@app.route("/api/news/refresh", methods=["POST"])
def refresh_news():
    try:
        import threading
        import sys

        def run_crew():
            try:
                sys.path.insert(0, ".")
                from news_crew import run_full_crew

                run_full_crew()
            except Exception as e:
                print(f"Crew execution error: {e}")

        thread = threading.Thread(target=run_crew)
        thread.start()

        return jsonify({"success": True, "message": "News refresh started"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/news/status")
def news_status():
    try:
        conn = get_news_db()
        c = conn.cursor()
        c.execute("SELECT value FROM news_metadata WHERE key = 'last_update'")
        row = c.fetchone()
        last_update = row["value"] if row else None

        c.execute("SELECT COUNT(*) FROM news_cache WHERE is_processed = TRUE")
        count = c.fetchone()[0]
        conn.close()

        return jsonify({"last_update": last_update, "cached_count": count})
    except Exception as e:
        return jsonify({"error": str(e)})


def scheduled_news_update():
    print("\n" + "=" * 50)
    print("⏰ Scheduled News Update")
    print("=" * 50)
    try:
        import sys

        sys.path.insert(0, ".")
        from news_crew import run_full_crew

        run_full_crew()
        print("=" * 50)
    except Exception as e:
        print(f"Scheduled update error: {e}")
        print("=" * 50)


scheduler = BackgroundScheduler()


def start_scheduler():
    init_news_db()

    try:
        scheduler.add_job(
            scheduled_news_update,
            "interval",
            hours=8,
            id="news_update",
            replace_existing=True,
        )
        scheduler.start()
        print("✅ News scheduler started (every 8 hours)")
    except Exception as e:
        print(f"Scheduler error: {e}")


if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or __name__ == "__main__":
    start_scheduler()


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/<path:filename>")
def serve_static(filename):
    if filename.endswith(".mp3"):
        return send_from_directory(".", filename, mimetype="audio/mpeg")
    return send_from_directory(".", filename)


# ==========================================
# STARTUP INITIALIZATION (Works with gunicorn)
# ==========================================


def initialize_app():
    """Initialize app - runs both with python app.py AND gunicorn"""
    print("\n" + "=" * 50)
    print("🚀 INITIALIZING PORTFOLIO")
    print("=" * 50)

    # Verify database connection
    verify_db_connection()

    # Initialize database tables if connected
    if DATABASE_AVAILABLE:
        init_db()

    # Show config status
    check_startup_config()

    print("=" * 50 + "\n")


# Run initialization at module load (works with gunicorn)
initialize_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    print(f"\n✅ Flask server starting on {host}:{port}")
    print(f"📋 Admin panel: http://localhost:{port}/ahmadAdmin")
    print(f"📰 ahmadAI News: http://localhost:{port}/ahmadAI")
    app.run(host=host, port=port, debug=False)
