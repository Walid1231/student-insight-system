from models import StudentAlert, StudentProfile, TeacherAssignment

def calculate_student_overview_stats(students, alerts=None):
    """
    Calculates summary statistics for a list of students.
    """
    total_students = len(students)
    if total_students == 0:
        return {
            'total_students': 0,
            'good_count': 0,
            'average_count': 0,
            'at_risk_count': 0,
            'alerts_count': 0,
            'good_percent': 0,
            'average_percent': 0,
            'at_risk_percent': 0,
            'class_distribution': {},
            'section_distribution': {},
            'subject_distribution': {},
        }

    good_count = sum(1 for s in students if s.performance_status == 'good')
    average_count = sum(1 for s in students if s.performance_status == 'average')
    at_risk_count = sum(1 for s in students if s.performance_status == 'at-risk')
    
    alerts_count = len(alerts) if alerts else 0

    # Distribution by class
    class_distribution = {}
    for s in students:
        if s.class_level:
            class_distribution[s.class_level] = class_distribution.get(s.class_level, 0) + 1
    
    # Distribution by section
    section_distribution = {}
    for s in students:
        if s.class_level and s.section:
            key = f"{s.class_level}-{s.section}"
            section_distribution[key] = section_distribution.get(key, 0) + 1

    return {
        'total_students': total_students,
        'good_count': good_count,
        'average_count': average_count,
        'at_risk_count': at_risk_count,
        'alerts_count': alerts_count,
        'good_percent': round((good_count / total_students * 100), 1),
        'average_percent': round((average_count / total_students * 100), 1),
        'at_risk_percent': round((at_risk_count / total_students * 100), 1),
        'class_distribution': class_distribution,
        'section_distribution': section_distribution
    }

def get_student_academic_summary(student):
    """
    Returns a dictionary summary of student's key academic metrics.
    """
    if not student:
        return {}
    
    return {
        "id": student.id,
        "name": student.full_name,
        "cgpa": student.current_cgpa,
        "department": student.department,
        "class_level": student.class_level, 
        "section": student.section,
        "status": student.performance_status,
        "metric": student.academic_metrics
    }
