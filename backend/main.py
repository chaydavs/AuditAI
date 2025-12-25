"""
VT Academic Optimizer - Backend API
===================================
A FastAPI server that:
1. User authentication (signup/login with JWT)
2. Accepts DARS audit uploads (PDF/TXT)
3. Extracts courses using AI (Gemini)
4. Tracks prerequisites with Neo4j
5. Returns what courses you can take next
6. Shows professor grade history
7. Saves user audit data to database

Run: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

import os
import json
import re
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict
from dotenv import load_dotenv
import jwt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# Email Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
APP_URL = os.getenv("APP_URL", "http://localhost:5173")
EMAIL_FROM = os.getenv("EMAIL_FROM", "VT Optimizer <onboarding@resend.dev>")

security = HTTPBearer(auto_error=False)


# =============================================================================
# DATA MODELS
# =============================================================================

class Course(BaseModel):
    code: str
    name: Optional[str] = None
    grade: Optional[str] = None
    term: Optional[str] = None
    credits: Optional[int] = None

class AuditResult(BaseModel):
    student_id: Optional[str] = None
    major: Optional[str] = None
    completed: List[Course] = []
    in_progress: List[Course] = []

class ProfessorStats(BaseModel):
    name: str
    course: str
    avg_gpa: float
    total_students: int
    grade_distribution: Dict[str, int]

class RoadmapResponse(BaseModel):
    taken: List[str]
    available: List[dict]
    locked: List[dict]

# Auth Models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    major: str = "CS"  # Default to CS
    minor: Optional[str] = None  # Optional minor
    concentration: Optional[str] = None  # Optional concentration/option within major
    start_year: int = 2024  # Year started at VT
    grad_year: int = 2028  # Expected graduation year

    @validator('password')
    def password_strong(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v) > 128:
            raise ValueError('Password too long')
        return v

    @validator('name')
    def name_valid(cls, v):
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Name is required')
        if len(v) > 100:
            raise ValueError('Name too long')
        return v

    @validator('major')
    def major_valid(cls, v):
        v = v.strip().upper()
        if len(v) < 1:
            raise ValueError('Major is required')
        return v

    @validator('minor')
    def minor_valid(cls, v):
        if v is None or v == "" or v == "NONE":
            return None
        return v.strip().upper()

    @validator('concentration')
    def concentration_valid(cls, v):
        if v is None or v == "" or v == "NONE":
            return None
        return v.strip().upper()

    @validator('start_year', 'grad_year')
    def year_valid(cls, v):
        if v < 2000 or v > 2040:
            raise ValueError('Invalid year')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @validator('password')
    def password_not_empty(cls, v):
        if not v:
            raise ValueError('Password is required')
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class VerifyEmailRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

# Plan Models
class PlanCreate(BaseModel):
    name: str
    plan_data: Dict[str, List[str]]  # {"fall1": ["CS 1114", ...], ...}
    is_default: bool = False

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    plan_data: Optional[Dict[str, List[str]]] = None
    is_default: Optional[bool] = None

class PlanResponse(BaseModel):
    id: int
    name: str
    plan_data: Dict[str, List[str]]
    is_default: bool
    created_at: str
    updated_at: str

class SharePlanRequest(BaseModel):
    plan_id: int
    student_name: Optional[str] = None
    expires_days: Optional[int] = 30  # Default 30 days


# =============================================================================
# DATABASE SETUP (SQLite for users)
# =============================================================================

DB_PATH = "users.db"

def init_sqlite():
    """Initialize SQLite database for users"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            major TEXT DEFAULT 'CS',
            minor TEXT DEFAULT NULL,
            concentration TEXT DEFAULT NULL,
            start_year INTEGER DEFAULT 2024,
            grad_year INTEGER DEFAULT 2028,
            email_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add columns if they don't exist (migration)
    migrations = [
        "ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN major TEXT DEFAULT 'CS'",
        "ALTER TABLE users ADD COLUMN minor TEXT DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN concentration TEXT DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN start_year INTEGER DEFAULT 2024",
        "ALTER TABLE users ADD COLUMN grad_year INTEGER DEFAULT 2028",
    ]
    for migration in migrations:
        try:
            cursor.execute(migration)
        except:
            pass  # Column already exists

    # Tokens table for email verification and password reset
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            token_type TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Saved audits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            major TEXT,
            completed TEXT,
            in_progress TEXT,
            roadmap TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Saved plans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            plan_data TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Shared plans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shared_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            share_token TEXT UNIQUE NOT NULL,
            student_name TEXT,
            expires_at TIMESTAMP,
            view_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES plans(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✓ SQLite database initialized")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, hashed = stored_hash.split(':')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return new_hash.hex() == hashed
    except:
        return False

def create_token(user_id: int, email: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current user from JWT token (optional)"""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return payload
    except:
        return None

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Require authentication"""
    if not credentials:
        raise HTTPException(401, "Authentication required")
    return decode_token(credentials.credentials)


# =============================================================================
# EMAIL & TOKEN FUNCTIONS
# =============================================================================

def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def create_verification_token(user_id: int) -> str:
    """Create an email verification token"""
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(hours=24)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tokens (user_id, token, token_type, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, token, "email_verification", expires_at)
    )
    conn.commit()
    conn.close()

    return token

def create_password_reset_token(user_id: int) -> str:
    """Create a password reset token"""
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry

    conn = get_db()
    cursor = conn.cursor()

    # Invalidate any existing reset tokens for this user
    cursor.execute(
        "UPDATE tokens SET used = 1 WHERE user_id = ? AND token_type = 'password_reset' AND used = 0",
        (user_id,)
    )

    cursor.execute(
        "INSERT INTO tokens (user_id, token, token_type, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, token, "password_reset", expires_at)
    )
    conn.commit()
    conn.close()

    return token

def verify_token(token: str, token_type: str) -> Optional[int]:
    """Verify a token and return user_id if valid"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT user_id, expires_at FROM tokens
           WHERE token = ? AND token_type = ? AND used = 0""",
        (token, token_type)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Check if expired
    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.utcnow() > expires_at:
        return None

    return row["user_id"]

def mark_token_used(token: str):
    """Mark a token as used"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE tokens SET used = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def send_verification_email(email: str, name: str, token: str) -> bool:
    """Send email verification email"""
    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY not set, skipping email")
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY

        verification_url = f"{APP_URL}/verify-email?token={token}"

        resend.Emails.send({
            "from": EMAIL_FROM,
            "to": [email],
            "subject": "Verify your VT Optimizer account",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #f97316, #ec4899); padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">VT Optimizer</h1>
                </div>
                <div style="padding: 30px; background: #f8fafc;">
                    <h2 style="color: #1e293b;">Hey {name}! 👋</h2>
                    <p style="color: #475569; font-size: 16px;">
                        Thanks for signing up for VT Optimizer! Please verify your email address by clicking the button below.
                    </p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}"
                           style="background: linear-gradient(135deg, #f97316, #ec4899);
                                  color: white;
                                  padding: 14px 32px;
                                  text-decoration: none;
                                  border-radius: 8px;
                                  font-weight: bold;
                                  display: inline-block;">
                            Verify Email
                        </a>
                    </div>
                    <p style="color: #94a3b8; font-size: 14px;">
                        This link expires in 24 hours. If you didn't create an account, you can ignore this email.
                    </p>
                </div>
                <div style="padding: 20px; text-align: center; background: #e2e8f0;">
                    <p style="color: #64748b; font-size: 12px; margin: 0;">
                        VT Academic Optimizer - Plan your path to graduation
                    </p>
                </div>
            </div>
            """
        })
        print(f"✓ Verification email sent to {email}")
        return True

    except Exception as e:
        print(f"✗ Failed to send verification email: {e}")
        return False

def send_password_reset_email(email: str, name: str, token: str) -> bool:
    """Send password reset email"""
    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY not set, skipping email")
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY

        reset_url = f"{APP_URL}/reset-password?token={token}"

        resend.Emails.send({
            "from": EMAIL_FROM,
            "to": [email],
            "subject": "Reset your VT Optimizer password",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #f97316, #ec4899); padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">VT Optimizer</h1>
                </div>
                <div style="padding: 30px; background: #f8fafc;">
                    <h2 style="color: #1e293b;">Password Reset Request</h2>
                    <p style="color: #475569; font-size: 16px;">
                        Hey {name}, we received a request to reset your password. Click the button below to set a new password.
                    </p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}"
                           style="background: linear-gradient(135deg, #f97316, #ec4899);
                                  color: white;
                                  padding: 14px 32px;
                                  text-decoration: none;
                                  border-radius: 8px;
                                  font-weight: bold;
                                  display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    <p style="color: #94a3b8; font-size: 14px;">
                        This link expires in 1 hour. If you didn't request a password reset, you can safely ignore this email.
                    </p>
                </div>
                <div style="padding: 20px; text-align: center; background: #e2e8f0;">
                    <p style="color: #64748b; font-size: 12px; margin: 0;">
                        VT Academic Optimizer - Plan your path to graduation
                    </p>
                </div>
            </div>
            """
        })
        print(f"✓ Password reset email sent to {email}")
        return True

    except Exception as e:
        print(f"✗ Failed to send password reset email: {e}")
        return False


# =============================================================================
# CS CURRICULUM DATA (loaded from JSON file)
# =============================================================================

import csv
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
COURSES_FILE = DATA_DIR / "courses.json"

def load_courses_from_file() -> dict:
    """Load courses from JSON file, with fallback to hardcoded data"""
    try:
        if COURSES_FILE.exists():
            with open(COURSES_FILE, 'r') as f:
                data = json.load(f)

                # Handle both flat format and wrapped format
                if "courses" in data:
                    source_data = data["courses"]
                else:
                    source_data = data

                courses = {}
                for code, info in source_data.items():
                    courses[code] = {
                        "name": info.get("name", ""),
                        "prereqs": info.get("prereqs", []),
                        "coreqs": info.get("coreqs", []),
                        "credits": info.get("credits", 3),
                        "category": info.get("category", ""),
                        "difficulty": info.get("difficulty", 3),
                        "workload": info.get("workload", 3),
                        "tags": info.get("tags", []),
                        "professors": info.get("professors", []),
                        "description": info.get("description", ""),
                        "typically_offered": info.get("typically_offered", []),
                        "required_for": info.get("required_for", [])
                    }
                print(f"✓ Loaded {len(courses)} courses from {COURSES_FILE}")
                return courses
    except Exception as e:
        print(f"✗ Error loading courses: {e}")

    # Fallback to hardcoded minimal data
    return {
        "CS 1114": {"name": "Intro to Software Design", "prereqs": [], "credits": 3},
        "CS 2114": {"name": "Software Design & Data Structures", "prereqs": ["CS 1114"], "credits": 3},
        "CS 2505": {"name": "Computer Organization I", "prereqs": ["CS 1114"], "credits": 3},
        "CS 2506": {"name": "Computer Organization II", "prereqs": ["CS 2505", "CS 2114"], "credits": 3},
        "CS 3114": {"name": "Data Structures & Algorithms", "prereqs": ["CS 2114", "CS 2505"], "credits": 3},
        "CS 3214": {"name": "Computer Systems", "prereqs": ["CS 2506", "CS 3114"], "credits": 3},
        "CS 4104": {"name": "Data & Algorithm Analysis", "prereqs": ["CS 3114", "MATH 2114"], "credits": 3},
        "MATH 1225": {"name": "Calculus I", "prereqs": [], "credits": 3},
        "MATH 1226": {"name": "Calculus II", "prereqs": ["MATH 1225"], "credits": 3},
        "MATH 2114": {"name": "Linear Algebra", "prereqs": ["MATH 1226"], "credits": 3},
    }

def save_courses_to_file(courses: dict):
    """Save courses back to JSON file"""
    DATA_DIR.mkdir(exist_ok=True)

    try:
        existing_data = {}
        if COURSES_FILE.exists():
            with open(COURSES_FILE, 'r') as f:
                existing_data = json.load(f)

        existing_data["courses"] = courses
        existing_data["metadata"] = existing_data.get("metadata", {})
        existing_data["metadata"]["last_updated"] = datetime.now().isoformat()

        with open(COURSES_FILE, 'w') as f:
            json.dump(existing_data, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving courses: {e}")
        return False

def import_courses_from_csv(csv_content: str) -> tuple[int, list]:
    """Import courses from CSV content, returns (count, errors)"""
    global CS_COURSES

    errors = []
    imported = 0

    try:
        reader = csv.DictReader(csv_content.strip().split('\n'))

        for row in reader:
            try:
                code = row.get('code', '').strip()
                if not code:
                    continue

                # Parse prereqs (comma-separated within quotes)
                prereqs_str = row.get('prereqs', '').strip()
                prereqs = [p.strip() for p in prereqs_str.split(',') if p.strip()] if prereqs_str else []

                # Parse coreqs
                coreqs_str = row.get('coreqs', '').strip()
                coreqs = [c.strip() for c in coreqs_str.split(',') if c.strip()] if coreqs_str else []

                # Parse tags
                tags_str = row.get('tags', '').strip()
                tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

                CS_COURSES[code] = {
                    "name": row.get('name', '').strip(),
                    "credits": int(row.get('credits', 3)),
                    "prereqs": prereqs,
                    "coreqs": coreqs,
                    "category": row.get('category', '').strip(),
                    "difficulty": int(row.get('difficulty', 3)),
                    "workload": int(row.get('workload', 3)),
                    "tags": tags,
                    "required_for": row.get('required_for', '').strip().split(',') if row.get('required_for') else [],
                    "professors": [],
                    "description": row.get('description', ''),
                    "typically_offered": []
                }
                imported += 1
            except Exception as e:
                errors.append(f"Row error: {e}")

        # Save to file
        save_courses_to_file(CS_COURSES)

    except Exception as e:
        errors.append(f"CSV parsing error: {e}")

    return imported, errors

# Load courses at module level
CS_COURSES = load_courses_from_file()

PROFESSOR_DATA = [
    {"name": "Dr. McQuain", "course": "CS 2114", "avg_gpa": 3.2, "total_students": 450,
     "grade_distribution": {"A": 120, "B": 180, "C": 100, "D": 30, "F": 20}},
    {"name": "Dr. Shaffer", "course": "CS 2114", "avg_gpa": 2.9, "total_students": 380,
     "grade_distribution": {"A": 80, "B": 140, "C": 110, "D": 30, "F": 20}},
    {"name": "Dr. Back", "course": "CS 3114", "avg_gpa": 3.1, "total_students": 320,
     "grade_distribution": {"A": 90, "B": 130, "C": 70, "D": 20, "F": 10}},
    {"name": "Dr. Butt", "course": "CS 3214", "avg_gpa": 2.8, "total_students": 280,
     "grade_distribution": {"A": 50, "B": 100, "C": 90, "D": 25, "F": 15}},
    {"name": "Dr. Cao", "course": "CS 4804", "avg_gpa": 3.4, "total_students": 150,
     "grade_distribution": {"A": 60, "B": 55, "C": 25, "D": 7, "F": 3}},
    {"name": "Dr. Edwards", "course": "CS 3304", "avg_gpa": 3.0, "total_students": 200,
     "grade_distribution": {"A": 50, "B": 80, "C": 50, "D": 15, "F": 5}},
    {"name": "Dr. Fox", "course": "CS 4104", "avg_gpa": 2.7, "total_students": 180,
     "grade_distribution": {"A": 30, "B": 60, "C": 60, "D": 20, "F": 10}},
    {"name": "Dr. Ramakrishnan", "course": "CS 4604", "avg_gpa": 3.3, "total_students": 220,
     "grade_distribution": {"A": 70, "B": 90, "C": 45, "D": 10, "F": 5}},
]


# =============================================================================
# NEO4J DATABASE (Optional)
# =============================================================================

neo4j_driver = None

async def init_neo4j():
    """Initialize Neo4j connection if available"""
    global neo4j_driver
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    try:
        from neo4j import AsyncGraphDatabase
        neo4j_driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        async with neo4j_driver.session() as session:
            await session.run("RETURN 1")
        print("✓ Connected to Neo4j")
        return True
    except Exception as e:
        print(f"✗ Neo4j not available: {e}")
        print("  Running in memory-only mode")
        neo4j_driver = None
        return False

async def close_neo4j():
    global neo4j_driver
    if neo4j_driver:
        await neo4j_driver.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown"""
    init_sqlite()
    await init_neo4j()
    yield
    await close_neo4j()


# =============================================================================
# APP SETUP
# =============================================================================

app = FastAPI(
    title="VT Academic Optimizer",
    description="Upload your DARS audit → Get your course roadmap",
    version="3.0.0",
    lifespan=lifespan
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# AUTH ENDPOINTS
# =============================================================================

@app.post("/auth/signup")
@limiter.limit("5/minute")
async def signup(request: Request, data: UserSignup):
    """Create a new user account"""
    conn = get_db()
    cursor = conn.cursor()

    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (data.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(400, "Email already registered")

    # Create user
    password_hash = hash_password(data.password)
    cursor.execute(
        "INSERT INTO users (email, password_hash, name, major, minor, concentration, start_year, grad_year, email_verified) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)",
        (data.email, password_hash, data.name, data.major, data.minor, data.concentration, data.start_year, data.grad_year)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Create verification token and send email
    verification_token = create_verification_token(user_id)
    send_verification_email(data.email, data.name, verification_token)

    # Create auth token
    token = create_token(user_id, data.email)

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email,
            "name": data.name,
            "major": data.major,
            "minor": data.minor,
            "concentration": data.concentration,
            "start_year": data.start_year,
            "grad_year": data.grad_year,
            "email_verified": False
        },
        "message": "Account created! Please check your email to verify your account."
    }


@app.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, data: UserLogin):
    """Login with email and password"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, password_hash, name, major, minor, concentration, start_year, grad_year, email_verified FROM users WHERE email = ?", (data.email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")

    token = create_token(user["id"], user["email"])

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "major": user["major"] or "CS",
            "minor": user["minor"],
            "concentration": user["concentration"],
            "start_year": user["start_year"] or 2024,
            "grad_year": user["grad_year"] or 2028,
            "email_verified": bool(user["email_verified"]) if user["email_verified"] is not None else False
        }
    }


@app.post("/auth/verify-email")
async def verify_email(data: VerifyEmailRequest):
    """Verify email address with token"""
    user_id = verify_token(data.token, "email_verification")

    if not user_id:
        raise HTTPException(400, "Invalid or expired verification token")

    # Mark email as verified
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    # Mark token as used
    mark_token_used(data.token)

    return {"success": True, "message": "Email verified successfully!"}


@app.post("/auth/resend-verification")
async def resend_verification(data: ResendVerificationRequest):
    """Resend verification email"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email_verified FROM users WHERE email = ?", (data.email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        # Don't reveal if email exists
        return {"success": True, "message": "If this email is registered, a verification link has been sent."}

    if user["email_verified"]:
        return {"success": True, "message": "Email is already verified."}

    # Create new verification token and send
    token = create_verification_token(user["id"])
    send_verification_email(data.email, user["name"], token)

    return {"success": True, "message": "Verification email sent!"}


@app.post("/auth/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest):
    """Request password reset email"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM users WHERE email = ?", (data.email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        # Don't reveal if email exists - always return success
        return {"success": True, "message": "If this email is registered, a password reset link has been sent."}

    # Create reset token and send email
    token = create_password_reset_token(user["id"])
    send_password_reset_email(data.email, user["name"], token)

    return {"success": True, "message": "Password reset email sent!"}


@app.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password with token"""
    if len(data.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    user_id = verify_token(data.token, "password_reset")

    if not user_id:
        raise HTTPException(400, "Invalid or expired reset token")

    # Update password
    password_hash = hash_password(data.new_password)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    conn.close()

    # Mark token as used
    mark_token_used(data.token)

    return {"success": True, "message": "Password reset successfully!"}


@app.get("/auth/me")
async def get_me(user: dict = Depends(require_auth)):
    """Get current user info"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, major, minor, concentration, start_year, grad_year, created_at FROM users WHERE id = ?", (user["user_id"],))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, "User not found")

    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "major": row["major"] or "CS",
        "minor": row["minor"],
        "concentration": row["concentration"],
        "start_year": row["start_year"] or 2024,
        "grad_year": row["grad_year"] or 2028,
        "created_at": row["created_at"]
    }


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    major: Optional[str] = None
    minor: Optional[str] = None
    concentration: Optional[str] = None
    start_year: Optional[int] = None
    grad_year: Optional[int] = None


@app.put("/auth/profile")
async def update_profile(data: ProfileUpdate, user: dict = Depends(require_auth)):
    """Update user profile"""
    conn = get_db()
    cursor = conn.cursor()

    updates = []
    params = []

    if data.name is not None:
        updates.append("name = ?")
        params.append(data.name.strip())

    if data.major is not None:
        updates.append("major = ?")
        params.append(data.major.strip().upper())

    if data.minor is not None:
        updates.append("minor = ?")
        # Handle "NONE" or empty string as null
        minor_val = data.minor.strip().upper() if data.minor.strip() and data.minor.strip().upper() != "NONE" else None
        params.append(minor_val)

    if data.concentration is not None:
        updates.append("concentration = ?")
        # Handle "NONE" or empty string as null
        conc_val = data.concentration.strip().upper() if data.concentration.strip() and data.concentration.strip().upper() != "NONE" else None
        params.append(conc_val)

    if data.start_year is not None:
        updates.append("start_year = ?")
        params.append(data.start_year)

    if data.grad_year is not None:
        updates.append("grad_year = ?")
        params.append(data.grad_year)

    if updates:
        params.append(user["user_id"])
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    conn.close()
    return {"success": True, "message": "Profile updated!"}


# =============================================================================
# PARSERS
# =============================================================================

# Import the comprehensive DARS parser
from dars_parser import parse_dars, dars_to_dict, DARSResult

def parse_audit_simple(text: str) -> AuditResult:
    """Extract courses using regex (fallback parser)"""
    pattern = r'(CS|MATH|STAT|ECE|PHYS|ENGL|CHEM|CMDA|ACIS|ECON|MGT|ARCH|BMES|SPES|NEUR)\s*(\d{4})'
    matches = re.findall(pattern, text, re.IGNORECASE)

    seen = set()
    courses = []
    for dept, num in matches:
        code = f"{dept.upper()} {num}"
        if code not in seen:
            seen.add(code)
            courses.append(Course(code=code))

    if not courses:
        raise ValueError("No courses found in the document")

    return AuditResult(major="Unknown", completed=courses)


def parse_audit_comprehensive(text: str) -> dict:
    """Parse DARS using comprehensive parser - returns full details"""
    result = parse_dars(text)
    return dars_to_dict(result)


def parse_audit_with_ai(text: str) -> AuditResult:
    """Use comprehensive parser first, fall back to AI if needed"""
    # Try comprehensive parser first
    try:
        result = parse_dars(text)
        if result.completed_courses or result.in_progress_courses:
            return AuditResult(
                major=result.major,
                completed=[Course(
                    code=c.code,
                    name=c.name,
                    grade=c.grade,
                    term=c.term_name,
                    credits=int(c.credits)
                ) for c in result.completed_courses],
                in_progress=[Course(
                    code=c.code,
                    name=c.name,
                    term=c.term_name,
                    credits=int(c.credits)
                ) for c in result.in_progress_courses]
            )
    except Exception as e:
        print(f"Comprehensive parser failed: {e}, trying AI parser")

    # Fall back to AI parser
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            "gemini-2.0-flash-lite",
            generation_config={"response_mime_type": "application/json", "temperature": 0.1}
        )

        prompt = """You are parsing a Virginia Tech DARS (Degree Audit Reporting System) document.

DARS FORMAT UNDERSTANDING:
- DARS shows degree requirements and course history
- Course entries look like: "23FA CS 1114 3.0 A Intro to Software Design"
- Term format: 23FA = Fall 2023, 24SP = Spring 2024, 25SU = Summer 2025
- IP = In Progress, W = Withdrawn, TR = Transfer, CB = Credit by Exam, P = Pass

EXTRACT AND RETURN THIS JSON:
{
    "major": "Computer Science",
    "completed": [
        {"code": "CS 1114", "name": "Intro to Software Design", "grade": "A", "term": "Fall 2023", "credits": 3}
    ],
    "in_progress": [
        {"code": "CS 2114", "name": "Software Design & Data Structures", "term": "Spring 2024", "credits": 3}
    ]
}

RULES:
1. Include courses with grades A-F, CB, TR, P as COMPLETED
2. Include courses with IP as IN_PROGRESS
3. Skip W (withdrawn) courses
4. Normalize course codes: "CS1114" → "CS 1114"

Virginia Tech DARS Document:
""" + text[:12000]

        response = model.generate_content(prompt)
        data = json.loads(response.text)

        return AuditResult(
            major=data.get("major"),
            completed=[Course(**c) for c in data.get("completed", [])],
            in_progress=[Course(**c) for c in data.get("in_progress", [])]
        )
    except Exception as e:
        raise ValueError(f"AI parsing failed: {str(e)}")


# =============================================================================
# ROADMAP LOGIC
# =============================================================================

def calculate_roadmap(taken_codes: List[str]) -> dict:
    """Calculate available and locked courses based on what's taken"""
    taken_set = set(c.upper().replace(" ", "").replace("-", "") for c in taken_codes)

    def normalize(code):
        return code.upper().replace(" ", "").replace("-", "")

    available = []
    locked = []

    for code, info in CS_COURSES.items():
        norm_code = normalize(code)
        if norm_code in taken_set:
            continue

        prereqs = info["prereqs"]
        missing = [p for p in prereqs if normalize(p) not in taken_set]

        if not missing:
            available.append({
                "code": code,
                "name": info["name"],
                "prerequisites": prereqs
            })
        else:
            locked.append({
                "code": code,
                "name": info["name"],
                "missing_prereqs": missing
            })

    available.sort(key=lambda x: x["code"])
    locked.sort(key=lambda x: x["code"])

    return {"taken": taken_codes, "available": available, "locked": locked}


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
def health_check():
    """Check if API is running"""
    return {
        "status": "ok",
        "message": "VT Academic Optimizer API",
        "database": "connected" if neo4j_driver else "in-memory"
    }


@app.post("/analyze")
async def analyze_audit(
    file: UploadFile = File(...),
    user: Optional[dict] = Depends(get_current_user)
):
    """Upload a DARS audit file and extract courses"""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    contents = await file.read()
    filename = file.filename.lower()

    # Extract text from file
    if filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(contents))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            raise HTTPException(400, f"Could not read PDF: {str(e)}")
    else:
        try:
            text = contents.decode("utf-8")
        except:
            raise HTTPException(400, "Could not read file as text")

    if not text.strip():
        raise HTTPException(400, "File is empty")

    # Try AI parser first, fall back to simple
    try:
        result = parse_audit_with_ai(text)
    except Exception as e:
        print(f"AI parser failed: {e}, using simple parser")
        result = parse_audit_simple(text)

    # Calculate roadmap
    taken_codes = [c.code for c in result.completed] + [c.code for c in result.in_progress]
    roadmap = calculate_roadmap(taken_codes)

    # Save to database if user is logged in
    if user:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audits (user_id, major, completed, in_progress, roadmap) VALUES (?, ?, ?, ?, ?)",
            (
                user["user_id"],
                result.major,
                json.dumps([c.model_dump() for c in result.completed]),
                json.dumps([c.model_dump() for c in result.in_progress]),
                json.dumps(roadmap)
            )
        )
        conn.commit()
        conn.close()

    return {
        "success": True,
        "data": {
            **result.model_dump(),
            "roadmap": roadmap
        }
    }


@app.get("/my-audits")
async def get_my_audits(user: dict = Depends(require_auth)):
    """Get all saved audits for the current user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, major, completed, in_progress, roadmap, uploaded_at FROM audits WHERE user_id = ? ORDER BY uploaded_at DESC",
        (user["user_id"],)
    )
    rows = cursor.fetchall()
    conn.close()

    audits = []
    for row in rows:
        audits.append({
            "id": row["id"],
            "major": row["major"],
            "completed": json.loads(row["completed"]) if row["completed"] else [],
            "in_progress": json.loads(row["in_progress"]) if row["in_progress"] else [],
            "roadmap": json.loads(row["roadmap"]) if row["roadmap"] else {},
            "uploaded_at": row["uploaded_at"]
        })

    return {"audits": audits}


@app.post("/roadmap")
def get_roadmap(courses: List[str]):
    """Get available courses based on what you've taken"""
    return calculate_roadmap(courses)


@app.get("/professors/{course_code}")
async def get_professors(course_code: str):
    """Get professor grade history for a course"""
    code = course_code.upper().replace("-", " ")
    if " " not in code and len(code) > 2:
        code = code[:2] + " " + code[2:] if code[:2].isalpha() else code

    if neo4j_driver:
        try:
            async with neo4j_driver.session() as session:
                result = await session.run(
                    """
                    MATCH (p:Professor)-[t:TEACHES]->(c:Course {code: $code})
                    RETURN p.name as name, t.avg_gpa as avg_gpa,
                           t.total_students as total_students,
                           t.grade_distribution as grades
                    """,
                    code=code
                )
                professors = []
                async for record in result:
                    professors.append({
                        "name": record["name"],
                        "course": code,
                        "avg_gpa": record["avg_gpa"],
                        "total_students": record["total_students"],
                        "grade_distribution": json.loads(record["grades"]) if record["grades"] else {}
                    })
                if professors:
                    return {"course": code, "professors": professors}
        except Exception as e:
            print(f"Neo4j query failed: {e}")

    professors = [p for p in PROFESSOR_DATA if p["course"] == code]
    return {"course": code, "professors": professors}


@app.get("/courses")
async def list_courses(search: Optional[str] = None, category: Optional[str] = None):
    """List all courses in the curriculum with full details, with optional search and category filter"""
    courses = []
    search_lower = search.lower() if search else None

    for code, info in CS_COURSES.items():
        # Apply search filter
        if search_lower:
            name = info.get("name", "").lower()
            code_lower = code.lower()
            if search_lower not in code_lower and search_lower not in name:
                continue

        # Apply category filter
        if category and info.get("category", "") != category:
            continue

        courses.append({
            "code": code,
            "name": info.get("name", ""),
            "credits": info.get("credits", 3),
            "prereqs": info.get("prereqs", []),
            "coreqs": info.get("coreqs", []),
            "category": info.get("category", ""),
            "difficulty": info.get("difficulty", 3),
            "workload": info.get("workload", 3),
            "tags": info.get("tags", []),
            "professors": info.get("professors", []),
            "description": info.get("description", ""),
            "typically_offered": info.get("typically_offered", []),
            "required_for": info.get("required_for", [])
        })
    return {"courses": sorted(courses, key=lambda x: x["code"]), "total": len(courses)}


class CourseCreate(BaseModel):
    code: str
    name: str
    credits: int = 3
    prereqs: List[str] = []
    coreqs: List[str] = []
    category: str = ""
    difficulty: int = 3
    workload: int = 3
    tags: List[str] = []
    description: str = ""


@app.post("/courses")
async def add_course(course: CourseCreate):
    """Add a new course to the curriculum"""
    global CS_COURSES

    code = course.code.upper().strip()

    CS_COURSES[code] = {
        "name": course.name,
        "credits": course.credits,
        "prereqs": course.prereqs,
        "coreqs": course.coreqs,
        "category": course.category,
        "difficulty": course.difficulty,
        "workload": course.workload,
        "tags": course.tags,
        "description": course.description,
        "professors": [],
        "typically_offered": [],
        "required_for": []
    }

    save_courses_to_file(CS_COURSES)
    return {"success": True, "message": f"Course {code} added", "total_courses": len(CS_COURSES)}


@app.post("/courses/import-csv")
async def import_csv(file: UploadFile = File(...)):
    """Import courses from a CSV file"""
    contents = await file.read()
    csv_text = contents.decode('utf-8')

    imported, errors = import_courses_from_csv(csv_text)

    return {
        "success": len(errors) == 0,
        "imported": imported,
        "errors": errors,
        "total_courses": len(CS_COURSES)
    }


@app.delete("/courses/{course_code}")
async def delete_course(course_code: str):
    """Delete a course from the curriculum"""
    global CS_COURSES

    code = course_code.upper().replace("-", " ")
    if code not in CS_COURSES:
        raise HTTPException(404, f"Course {code} not found")

    del CS_COURSES[code]
    save_courses_to_file(CS_COURSES)

    return {"success": True, "message": f"Course {code} deleted"}


@app.post("/courses/refresh")
async def refresh_courses():
    """Refresh courses from the scraper with known VT CS courses"""
    global CS_COURSES

    try:
        # Import the scraper's known courses
        import sys
        scraper_path = Path(__file__).parent / "scraper"
        sys.path.insert(0, str(scraper_path))

        from vt_timetable_scraper import load_known_courses, save_courses

        # Load comprehensive known courses
        known_courses = load_known_courses()

        # Merge with existing (known courses take precedence)
        for code, data in known_courses.items():
            # Convert to our format
            CS_COURSES[code] = {
                "name": data.get("name", ""),
                "credits": data.get("credits", 3),
                "prereqs": data.get("prereqs", []),
                "coreqs": data.get("coreqs", []),
                "category": data.get("category", ""),
                "difficulty": data.get("difficulty", 3),
                "workload": data.get("workload", 3),
                "tags": data.get("tags", []),
                "professors": data.get("professors", []),
                "description": data.get("description", ""),
                "typically_offered": data.get("typically_offered", []),
                "required_for": data.get("required_for", [])
            }

        save_courses_to_file(CS_COURSES)

        return {
            "success": True,
            "message": f"Refreshed {len(known_courses)} courses",
            "total_courses": len(CS_COURSES)
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to refresh courses: {str(e)}")


class PlanAnalysisRequest(BaseModel):
    plan: Dict[str, List[str]]
    completed: List[str] = []
    in_progress: List[str] = []
    major: str = "CS"  # Default to CS
    minor: Optional[str] = None  # Optional minor


# Import the AI Advisor
from ai_advisor import advisor as vt_advisor, CAREER_PATHS

@app.post("/analyze-plan")
async def analyze_plan(data: PlanAnalysisRequest):
    """AI-powered analysis of a graduation plan using VT-specific rules"""
    try:
        analysis = await vt_advisor.analyze_plan(
            plan=data.plan,
            completed=data.completed,
            in_progress=data.in_progress,
            major=data.major,
            minor=data.minor
        )
        return {"success": True, "analysis": analysis, "major": data.major, "minor": data.minor}
    except Exception as e:
        print(f"Analysis error: {e}")
        return {"success": False, "error": str(e)}


class SuggestCoursesRequest(BaseModel):
    completed: List[str] = []
    current_plan: Dict[str, List[str]] = {}
    career_interest: Optional[str] = None


@app.post("/suggest-courses")
async def suggest_courses(data: SuggestCoursesRequest):
    """Get AI-powered course suggestions based on progress and career goals"""
    try:
        suggestions = vt_advisor.suggest_courses(
            completed=data.completed,
            current_plan=data.current_plan,
            career_interest=data.career_interest
        )
        return {
            "success": True,
            "suggestions": suggestions,
            "careerPaths": CAREER_PATHS
        }
    except Exception as e:
        print(f"Suggestion error: {e}")
        return {"success": False, "error": str(e)}


class SimulateCourseRequest(BaseModel):
    course: str
    semester: str
    current_plan: Dict[str, List[str]]
    completed: List[str] = []


@app.post("/simulate-course")
async def simulate_course(data: SimulateCourseRequest):
    """Simulate adding a course and see the impact on plan score"""
    try:
        result = await vt_advisor.simulate_addition(
            course=data.course,
            semester=data.semester,
            current_plan=data.current_plan,
            completed=data.completed
        )
        return {"success": True, "simulation": result}
    except Exception as e:
        print(f"Simulation error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/career-paths")
async def get_career_paths():
    """Get available career paths and their recommended courses"""
    return {"success": True, "careerPaths": CAREER_PATHS}


@app.get("/degree-requirements")
async def get_degree_requirements(major: Optional[str] = None):
    """Get degree requirements for a major (defaults to CS if not specified)"""
    from degree_requirements import get_requirements, SUPPORTED_MAJORS, check_graduation_progress

    major_code = (major or "CS").upper()
    req = get_requirements(major_code)

    if req:
        return {
            "success": True,
            "major": req.major_name,
            "major_code": req.major_code,
            "college": req.college,
            "requirements": {
                "core_courses": req.core_courses,
                "choice_requirements": req.choice_requirements,
                "elective_requirements": req.elective_requirements,
                "math_requirements": req.math_requirements,
                "science_requirements": req.science_requirements,
                "pathways_credits": req.pathways_credits,
                "total_credits": req.total_credits,
                "recommended_sequence": req.recommended_sequence,
                "difficulty_ratings": req.difficulty_ratings,
            }
        }
    else:
        # Fallback to generic requirements for unsupported majors
        from ai_advisor import DegreeRequirement as OldDegreeRequirement
        return {
            "success": True,
            "major": "Computer Science",
            "major_code": "CS",
            "requirements": {
                "core_courses": OldDegreeRequirement.CS_CORE,
                "math_requirements": OldDegreeRequirement.MATH_CORE,
                "total_credits": OldDegreeRequirement.TOTAL_CREDITS
            }
        }


@app.get("/majors")
async def get_majors():
    """Get list of all supported majors"""
    from degree_requirements import SUPPORTED_MAJORS
    return {
        "success": True,
        "majors": SUPPORTED_MAJORS
    }


@app.get("/minors")
async def get_minors():
    """Get list of all supported minors"""
    from degree_requirements import SUPPORTED_MINORS
    return {
        "success": True,
        "minors": SUPPORTED_MINORS
    }


@app.get("/concentrations")
async def get_concentrations(major: str):
    """Get available concentrations for a specific major"""
    from degree_requirements import get_concentrations
    concentrations = get_concentrations(major)
    return {
        "success": True,
        "major": major.upper(),
        "concentrations": concentrations,
        "has_concentrations": len(concentrations) > 0
    }


@app.get("/graduation-progress")
async def get_graduation_progress(
    major: str,
    user: dict = Depends(require_auth)
):
    """Check graduation progress for a user"""
    from degree_requirements import check_graduation_progress

    # Get user's completed courses from their plans
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT plan_data FROM plans WHERE user_id = ? AND is_default = 1",
        (user["user_id"],)
    )
    row = cursor.fetchone()
    conn.close()

    completed = []
    if row and row["plan_data"]:
        plan_data = json.loads(row["plan_data"])
        for semester, courses in plan_data.items():
            completed.extend(courses)

    progress = check_graduation_progress(major, completed)
    return {"success": True, "progress": progress}


# =============================================================================
# PLANS API
# =============================================================================

@app.get("/plans")
async def list_plans(user: dict = Depends(require_auth)):
    """Get all saved plans for the current user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, plan_data, is_default, created_at, updated_at FROM plans WHERE user_id = ? ORDER BY updated_at DESC",
        (user["user_id"],)
    )
    rows = cursor.fetchall()
    conn.close()

    plans = []
    for row in rows:
        plans.append({
            "id": row["id"],
            "name": row["name"],
            "plan_data": json.loads(row["plan_data"]) if row["plan_data"] else {},
            "is_default": bool(row["is_default"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })

    return {"plans": plans, "total": len(plans)}


@app.post("/plans")
async def create_plan(data: PlanCreate, user: dict = Depends(require_auth)):
    """Create a new plan"""
    conn = get_db()
    cursor = conn.cursor()

    # If this is set as default, unset other defaults
    if data.is_default:
        cursor.execute("UPDATE plans SET is_default = 0 WHERE user_id = ?", (user["user_id"],))

    cursor.execute(
        "INSERT INTO plans (user_id, name, plan_data, is_default) VALUES (?, ?, ?, ?)",
        (user["user_id"], data.name, json.dumps(data.plan_data), 1 if data.is_default else 0)
    )
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Plan '{data.name}' saved!",
        "plan": {
            "id": plan_id,
            "name": data.name,
            "plan_data": data.plan_data,
            "is_default": data.is_default
        }
    }


@app.get("/plans/{plan_id}")
async def get_plan(plan_id: int, user: dict = Depends(require_auth)):
    """Get a specific plan"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, plan_data, is_default, created_at, updated_at FROM plans WHERE id = ? AND user_id = ?",
        (plan_id, user["user_id"])
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, "Plan not found")

    return {
        "id": row["id"],
        "name": row["name"],
        "plan_data": json.loads(row["plan_data"]) if row["plan_data"] else {},
        "is_default": bool(row["is_default"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


@app.put("/plans/{plan_id}")
async def update_plan(plan_id: int, data: PlanUpdate, user: dict = Depends(require_auth)):
    """Update an existing plan"""
    conn = get_db()
    cursor = conn.cursor()

    # Check plan exists and belongs to user
    cursor.execute("SELECT id FROM plans WHERE id = ? AND user_id = ?", (plan_id, user["user_id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(404, "Plan not found")

    # Build update query dynamically
    updates = []
    params = []

    if data.name is not None:
        updates.append("name = ?")
        params.append(data.name)

    if data.plan_data is not None:
        updates.append("plan_data = ?")
        params.append(json.dumps(data.plan_data))

    if data.is_default is not None:
        if data.is_default:
            # Unset other defaults first
            cursor.execute("UPDATE plans SET is_default = 0 WHERE user_id = ?", (user["user_id"],))
        updates.append("is_default = ?")
        params.append(1 if data.is_default else 0)

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(plan_id)

    cursor.execute(f"UPDATE plans SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()

    return {"success": True, "message": "Plan updated!"}


@app.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, user: dict = Depends(require_auth)):
    """Delete a plan"""
    conn = get_db()
    cursor = conn.cursor()

    # Check plan exists and belongs to user
    cursor.execute("SELECT id FROM plans WHERE id = ? AND user_id = ?", (plan_id, user["user_id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(404, "Plan not found")

    cursor.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Plan deleted!"}


@app.get("/plans/default")
async def get_default_plan(user: dict = Depends(require_auth)):
    """Get the user's default plan"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, plan_data, is_default, created_at, updated_at FROM plans WHERE user_id = ? AND is_default = 1",
        (user["user_id"],)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"plan": None}

    return {
        "plan": {
            "id": row["id"],
            "name": row["name"],
            "plan_data": json.loads(row["plan_data"]) if row["plan_data"] else {},
            "is_default": True,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    }


# =============================================================================
# SHARE API
# =============================================================================

@app.post("/share")
async def create_share_link(data: SharePlanRequest, user: dict = Depends(require_auth)):
    """Generate a shareable link for a plan"""
    conn = get_db()
    cursor = conn.cursor()

    # Verify plan belongs to user
    cursor.execute("SELECT id, name FROM plans WHERE id = ? AND user_id = ?", (data.plan_id, user["user_id"]))
    plan = cursor.fetchone()
    if not plan:
        conn.close()
        raise HTTPException(404, "Plan not found")

    # Generate unique share token
    share_token = secrets.token_urlsafe(16)

    # Calculate expiry
    expires_at = None
    if data.expires_days:
        expires_at = (datetime.utcnow() + timedelta(days=data.expires_days)).isoformat()

    # Get user name for student_name if not provided
    cursor.execute("SELECT name FROM users WHERE id = ?", (user["user_id"],))
    user_row = cursor.fetchone()
    student_name = data.student_name or user_row["name"]

    cursor.execute(
        "INSERT INTO shared_plans (plan_id, user_id, share_token, student_name, expires_at) VALUES (?, ?, ?, ?, ?)",
        (data.plan_id, user["user_id"], share_token, student_name, expires_at)
    )
    conn.commit()
    conn.close()

    share_url = f"{APP_URL}/shared/{share_token}"

    return {
        "success": True,
        "share_token": share_token,
        "share_url": share_url,
        "expires_at": expires_at,
        "plan_name": plan["name"]
    }


@app.get("/shared/{share_token}")
async def get_shared_plan(share_token: str):
    """View a shared plan (public, no auth required)"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sp.id, sp.plan_id, sp.student_name, sp.expires_at, sp.view_count,
               p.name as plan_name, p.plan_data
        FROM shared_plans sp
        JOIN plans p ON sp.plan_id = p.id
        WHERE sp.share_token = ?
    """, (share_token,))
    share = cursor.fetchone()

    if not share:
        conn.close()
        raise HTTPException(404, "Shared plan not found or expired")

    # Check if expired
    if share["expires_at"]:
        expires = datetime.fromisoformat(share["expires_at"])
        if datetime.utcnow() > expires:
            conn.close()
            raise HTTPException(410, "This shared link has expired")

    # Increment view count
    cursor.execute("UPDATE shared_plans SET view_count = view_count + 1 WHERE id = ?", (share["id"],))
    conn.commit()
    conn.close()

    return {
        "student_name": share["student_name"],
        "plan_name": share["plan_name"],
        "plan_data": json.loads(share["plan_data"]) if share["plan_data"] else {},
        "view_count": share["view_count"] + 1
    }


@app.get("/my-shares")
async def list_my_shares(user: dict = Depends(require_auth)):
    """List all shared links created by user"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sp.id, sp.share_token, sp.student_name, sp.expires_at, sp.view_count, sp.created_at,
               p.name as plan_name
        FROM shared_plans sp
        JOIN plans p ON sp.plan_id = p.id
        WHERE sp.user_id = ?
        ORDER BY sp.created_at DESC
    """, (user["user_id"],))
    rows = cursor.fetchall()
    conn.close()

    shares = []
    for row in rows:
        shares.append({
            "id": row["id"],
            "share_token": row["share_token"],
            "share_url": f"{APP_URL}/shared/{row['share_token']}",
            "student_name": row["student_name"],
            "plan_name": row["plan_name"],
            "expires_at": row["expires_at"],
            "view_count": row["view_count"],
            "created_at": row["created_at"]
        })

    return {"shares": shares}


@app.delete("/share/{share_id}")
async def delete_share(share_id: int, user: dict = Depends(require_auth)):
    """Delete a share link"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM shared_plans WHERE id = ? AND user_id = ?", (share_id, user["user_id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(404, "Share not found")

    cursor.execute("DELETE FROM shared_plans WHERE id = ?", (share_id,))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Share link deleted"}


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
