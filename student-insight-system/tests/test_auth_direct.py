import requests
import random
import string

# Test signup and login directly
BASE_URL = "http://localhost:5000"

def random_email():
    return f"test_{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"

# Test Signup
print("=" * 60)
print("TESTING SIGNUP")
print("=" * 60)

signup_data = {
    "name": "Test Student",
    "email": random_email(),
    "password": "testpassword123",
    "role": "student"
}

print(f"Sending signup request for: {signup_data['email']}")
resp = requests.post(f"{BASE_URL}/register", data=signup_data)
print(f"Response Status: {resp.status_code}")
print(f"Response Body: {resp.text}")

# Test Login
print("\n" + "=" * 60)
print("TESTING LOGIN")
print("=" * 60)

login_data = {
    "email": signup_data["email"],
    "password": signup_data["password"],
    "role": "student"
}

print(f"Sending login request for: {login_data['email']}")
resp = requests.post(f"{BASE_URL}/login", data=login_data)
print(f"Response Status: {resp.status_code}")
print(f"Response Body: {resp.text}")
print(f"Cookies: {resp.cookies}")

print("\n" + "=" * 60)
