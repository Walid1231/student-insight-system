import requests
import re

BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/login"
DASHBOARD_URL = f"{BASE_URL}/student/dashboard/v2"
PROFILE_URL = f"{BASE_URL}/student/profile"

# Start session
s = requests.Session()

# 1. Login
print("Logging in...")
# Need to get CSRF token first if enabled, but let's try direct post or check login page
login_page = s.get(LOGIN_URL)
# Assuming no CSRF for now or simple form
login_data = {'email': 'student@example.com', 'password': 'password123'} # Try default seed creds? 
# or register? 
# Let's try to register a new user to be sure
REGISTER_URL = f"{BASE_URL}/register"
reg_data = {
    'full_name': 'Test User',
    'email': 'verify_nav@example.com',
    'password': 'password123',
    'confirm_password': 'password123',
    'role': 'student'
}
print("Registering new user...")
r_reg = s.post(REGISTER_URL, data=reg_data)
# If already exists, try login
r_login = s.post(LOGIN_URL, data={'email': 'verify_nav@example.com', 'password': 'password123'})

if r_login.status_code != 200:
    print(f"Login failed: {r_login.status_code}")
    # Try existing testuser
    r_login = s.post(LOGIN_URL, data={'email': 'student@example.com', 'password': 'password123'})

# 2. Check Dashboard
print("Checking Dashboard V2...")
r_dash = s.get(DASHBOARD_URL)
if r_dash.status_code == 200:
    content = r_dash.text
    if 'static/css/global.css' in content:
        print("[PASS] Global CSS link found in Dashboard.")
    else:
        print("[FAIL] Global CSS link NOT found in Dashboard.")
    
    if 'hx-boost="true"' in content:
        print("[PASS] HTMX boost attribute found in Dashboard sidebar.")
    else:
        print("[FAIL] HTMX boost attribute NOT found in Dashboard sidebar.")
else:
    print(f"[FAIL] Dashboard load failed: {r_dash.status_code}")

# 3. Check Profile
print("Checking Profile...")
r_prof = s.get(PROFILE_URL)
if r_prof.status_code == 200:
    content = r_prof.text
    if 'static/css/global.css' in content:
        print("[PASS] Global CSS link found in Profile.")
    else:
        print("[FAIL] Global CSS link NOT found in Profile.")
    
    # Check for absence of style block
    if '<style>' in content and '.profile-header' in content: 
         # Simple check, might have other styles
         print("[WARN] Style tag found, checking content...")
    else:
         print("[PASS] Large style block likely removed.")
else:
    print(f"[FAIL] Profile load failed: {r_prof.status_code}")
