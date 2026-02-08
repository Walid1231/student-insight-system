from flask import Flask, render_template, Blueprint

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'test'

# Mock Dashboard Blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    return "Profile Page"

@dashboard_bp.route('/student/create-profile', methods=['GET', 'POST'])
def create_profile():
    return "Create Profile Page"

app.register_blueprint(dashboard_bp)

# Dummy student data
class Student:
    def __init__(self):
        self.full_name = "Test Student"
        self.profile_picture = "default.jpg"
        self.university = "Test Uni"
        self.email = "test@example.com"
        self.department = "CS"
        self.current_year = "3rd Year"
        self.cgpa = 3.5
        self.career_goal = "Dev"
        self.bio = "Hello"
        self.linkedin_profile = "http://linkedin.com"
        self.github_profile = "http://github.com"

# Dummy dashboard data
data = {
    'name': 'Test',
    'department': 'CS',
    'year': '3rd',
    'university_name': 'Uni',
    'status': 'On Track',
    'cgpa': 3.8,
    'credits_completed': 100,
    'subjects': [],
    'careers': [],
    'skills_known': [],
    'skills_to_learn': [],
    'weekly_progress': [],
    'goal_percentage': 80,
    'goal_message': 'Good'
}

@app.route('/verify_profile')
def verify_profile():
    return render_template('student_profile.html', student=Student(), active_page='profile')

@app.route('/verify_dashboard')
def verify_dashboard():
    return render_template('student_dashboard_v2.html', data=data, active_page='dashboard')

if __name__ == "__main__":
    from jinja2.exceptions import TemplateSyntaxError
    
    print("Verifying student_profile.html...")
    try:
        with app.test_request_context('/verify_profile'):
            render_template('student_profile.html', student=Student(), active_page='profile')
        print("PASS: student_profile.html")
    except TemplateSyntaxError as e:
        print(f"FAIL: student_profile.html\nLine: {e.lineno}\nMessage: {e.message}\nFile: {e.filename}")
    except Exception as e:
        print(f"FAIL: student_profile.html\n{e}")

    print("\nVerifying student_dashboard_v2.html...")
    try:
        with app.test_request_context('/verify_dashboard'):
            render_template('student_dashboard_v2.html', data=data, active_page='dashboard')
        print("PASS: student_dashboard_v2.html")
    except TemplateSyntaxError as e:
        print(f"FAIL: student_dashboard_v2.html\nLine: {e.lineno}\nMessage: {e.message}\nFile: {e.filename}")
    except Exception as e:
        print(f"FAIL: student_dashboard_v2.html\n{e}")
