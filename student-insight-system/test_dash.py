import sys
sys.path.insert(0, '.')
from app import app
from models import User, StudentProfile
from flask_jwt_extended import create_access_token
import re

with app.app_context():
    student = StudentProfile.query.filter_by(full_name='Alice Smith').first()
    user = User.query.get(student.user_id)
    token = create_access_token(identity=str(user.id), additional_claims={'role': 'student'})
    
    with app.test_client() as client:
        client.set_cookie('access_token_cookie', token)
        resp = client.get('/student/dashboard')
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            html = resp.data.decode('utf-8')
            checks = {
                'CGPA Trend': 'cgpaTrendChart' in html,
                'Radar': 'radarChart' in html,
                'Core vs GED': 'coreGedChart' in html,
                'Weekly Hours': 'weeklyHoursChart' in html,
                'Skill Effort': 'skillEffortChart' in html,
                'Career Compat': 'career-compat-item' in html,
                'Burnout Gauge': 'burnoutGauge' in html,
                'Goal Curve': 'goalCurveChart' in html,
                'Student Name': 'Alice Smith' in html,
                'Real CGPA data': 'Sem 1' in html,
            }
            for name, ok in checks.items():
                sym = "PASS" if ok else "FAIL"
                print(f"  [{sym}] {name}")
            
            print(f"\n  HTML size: {len(html)} bytes")
            
            # Check CGPA value
            match = re.search(r'Current: ([\d.]+)', html)
            if match:
                print(f"  CGPA rendered: {match.group(1)}")
            
            # Check burnout value
            match = re.search(r'burnout_pct.*?(\d+)', html)
            if match:
                print(f"  Burnout pct in JS: {match.group(1)}")
            
            # Check for no errors
            if 'Internal Server Error' in html or 'Traceback' in html:
                print("  ERROR found in response!")
            else:
                print("  No errors detected")
        else:
            print(f"ERROR: {resp.data.decode('utf-8')[:500]}")
