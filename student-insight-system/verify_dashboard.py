import requests

BASE_URL = "http://127.0.0.1:5000"

def verify():
    session = requests.Session()
    
    # 1. Login
    login_url = f"{BASE_URL}/login"
    payload = {
        "email": "teacher@test.com",
        "password": "password",
        "role": "teacher" # Important if roles are enforced on login
    }
    
    print(f"Logging in to {login_url}...")
    try:
        # Check if GET works first (to verify server up)
        r = session.get(login_url)
        if r.status_code != 200:
            print(f"Start page status code: {r.status_code}")
            
        r = session.post(login_url, data=payload)
        print(f"Login Response: {r.status_code}")
        # print(r.text[:500]) # Debug
        
        # Check if JSON or Redirect
        try:
            json_resp = r.json()
            print("Login JSON:", json_resp)
            if json_resp.get("msg") == "Login successful":
                print("✅ API Login Successful")
            else:
                print("❌ API Login Failed")
                return
        except:
             print("Login returned verify non-JSON (likely HTML or redirect)")

    except Exception as e:
        print(f"❌ Login Request Failed: {e}")
        return

    # 2. Access Dashboard
    dashboard_url = f"{BASE_URL}/teacher/dashboard"
    print(f"Accessing {dashboard_url}...")
    
    try:
        r = session.get(dashboard_url)
        print(f"Dashboard Status: {r.status_code}")
        
        content = r.text
        
        # 3. Assertions
        checks = [
            ("Dr. Sarah Johnson", "Teacher Name"),
            ("Total Students", "Overview Card 1"),
            ("At Risk", "Overview Card 2"),
            ("Active Alerts", "Overview Card 3"),
            ("Assigned Students", "Student List Header"),
            ("performanceChart", "Chart Canvas"),
            ("Resolve", "Resolve Button logic/text") # Might be in JS or button
        ]
        
        all_passed = True
        for string, label in checks:
            if string in content:
                print(f"✅ Found {label}: '{string}'")
            else:
                print(f"❌ Missing {label}: '{string}'")
                all_passed = False
                
        if all_passed:
            print("\n🎉 Teacher Dashboard Verification PASSED!")
        else:
            print("\n⚠️  Some checks failed. See above.")
            
    except Exception as e:
        print(f"❌ Dashboard Request Failed: {e}")

    # 3. Access Student Detail
    # Assuming student ID 1 exists from populate script
    detail_url = f"{BASE_URL}/teacher/student/1"
    print(f"Accessing {detail_url}...")
    try:
        r = session.get(detail_url)
        content = r.text
        if r.status_code == 200:
            if "Teacher Notes" in content:
                print("✅ Found 'Teacher Notes' section")
            else:
                 print("❌ Missing 'Teacher Notes' section")
            
            if "Back to Dashboard" in content:
                print("✅ Found 'Back to Dashboard' link")
            else:
                print("❌ Missing Back link")
        else:
            print(f"❌ Student Detail failed with {r.status_code}")
    except Exception as e:
        print(f"❌ Detail Request Failed: {e}")

if __name__ == "__main__":
    verify()
