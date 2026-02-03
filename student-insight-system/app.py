import sqlite3
from flask import Flask, request, jsonify, render_template, make_response
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, 
    get_jwt, set_access_cookies
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['JWT_SECRET_KEY'] = 'super-secret-key-change-this-in-production' 
app.config['JWT_TOKEN_LOCATION'] = ['cookies'] 
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'     

jwt = JWTManager(app)
DB_NAME = "student_insight.db"

# --- DATABASE FUNCTIONS (SQLite3) ---

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database with the User table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Table using raw SQL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def seed_database():
    """Inserts 10 dummy users if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we already have users
    cursor.execute('SELECT count(*) FROM users')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    users_data = [
        # Students
        ("Alice Student", "alice@test.com", "pass123", "student"),
        ("Bob Scholar", "bob@test.com", "pass123", "student"),
        ("Charlie Learner", "charlie@test.com", "pass123", "student"),
        ("Diana Freshman", "diana@test.com", "pass123", "student"),
        ("Evan Senior", "evan@test.com", "pass123", "student"),
        # Teachers
        ("Prof. Smith", "smith@test.com", "teach123", "teacher"),
        ("Dr. Jones", "jones@test.com", "teach123", "teacher"),
        ("Ms. Davis", "davis@test.com", "teach123", "teacher"),
        ("Mr. Wilson", "wilson@test.com", "teach123", "teacher"),
        ("Dr. Brown", "brown@test.com", "teach123", "teacher"),
    ]

    print("--- SEEDING SQLITE DATABASE ---")
    for name, email, password, role in users_data:
        # Hash the password before storing
        hashed_pw = generate_password_hash(password)
        try:
            cursor.execute(
                'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                (name, email, hashed_pw, role)
            )
            print(f"Added: {name}")
        except sqlite3.IntegrityError:
            pass # Skip duplicates if any
            
    conn.commit()
    conn.close()
    print("--- SEEDING COMPLETE ---")

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"msg": "Email already registered"}), 400

    hashed_pw = generate_password_hash(password)
    cursor.execute(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        (name, email, hashed_pw, role)
    )
    conn.commit()
    conn.close()

    return jsonify({"msg": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find user by email
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if user is None or not check_password_hash(user['password'], password):
        return jsonify({"msg": "Invalid email or password"}), 401

    # Create JWT
    # user['id'] works because we set sqlite3.Row factory
    additional_claims = {"role": user['role'], "name": user['name']}
    access_token = create_access_token(identity=str(user['id']), additional_claims=additional_claims)

    resp = jsonify({"msg": "Login successful", "role": user['role']})
    set_access_cookies(resp, access_token)
    
    return resp, 200

# --- DASHBOARD ROUTES ---

@app.route('/student/dashboard')
@jwt_required()
def student_dashboard():
    claims = get_jwt()
    if claims['role'] != 'student':
        return "<h1>Access Denied: Not a student.</h1>", 403
    
    return f"""
    <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
        <h1 style="color: #002D62;">Welcome, {claims['name']}!</h1>
        <p>You have logged in as a <b>Student</b>.</p>
        <p><i>Running on Raw SQLite3 & JWT</i></p>
        <a href="/">Logout</a>
    </div>
    """

@app.route('/teacher/dashboard')
@jwt_required()
def teacher_dashboard():
    claims = get_jwt()
    if claims['role'] != 'teacher':
        return "<h1>Access Denied: Not a teacher.</h1>", 403
    
    return f"""
    <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
        <h1 style="color: #D4AF37;">Welcome, {claims['name']}!</h1>
        <p>You have logged in as a <b>Teacher</b>.</p>
        <p><i>Running on Raw SQLite3 & JWT</i></p>
        <a href="/">Logout</a>
    </div>
    """

if __name__ == '__main__':
    # Initialize DB table and seed data before running
    init_db()
    seed_database()
    app.run(debug=True, port=5000)