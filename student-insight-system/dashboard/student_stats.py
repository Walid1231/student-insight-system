# Helper functions for student detail calculations
from datetime import datetime, timedelta
from sqlalchemy import func

def calculate_attendance_stats(student_id):
    """Calculate attendance percentage and trend"""
    from models import Attendance
    
    total = Attendance.query.filter_by(student_id=student_id).count()
    if total == 0:
        return {'percentage': 0, 'trend': 'unknown', 'total': 0, 'present': 0}
    
    present = Attendance.query.filter_by(student_id=student_id, status='present').count()
    percentage = round((present / total) * 100, 1)
    
    # Calculate trend: compare last 10 vs previous 10
    recent_records = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc()).limit(20).all()
    
    if len(recent_records) >= 20:
        recent_10 = recent_records[:10]
        previous_10 = recent_records[10:20]
        
        recent_present = sum(1 for r in recent_10 if r.status == 'present')
        previous_present = sum(1 for r in previous_10 if r.status == 'present')
        
        recent_pct = (recent_present / 10) * 100
        previous_pct = (previous_present / 10) * 100
        
        if recent_pct > previous_pct + 5:
            trend = 'improving'
        elif recent_pct < previous_pct - 5:
            trend = 'declining'  
        else:
            trend = 'stable'
    else:
        trend = 'unknown'
    
    return {
        'percentage': percentage,
        'trend': trend,
        'total': total,
        'present': present,
        'recent': recent_records[:5]
    }

def calculate_assignment_stats(student_id):
    """Calculate assignment completion and average score"""
    from models import Assignment, AssignmentSubmission
    
    # Get all assignments
    total_assignments = Assignment.query.count()
    if total_assignments == 0:
        return {'completion_rate': 0, 'avg_score': 0, 'pending': 0, 'recent': []}
    
    # Get student's submissions
    submissions = AssignmentSubmission.query.filter_by(student_id=student_id).all()
    completed = len([s for s in submissions if s.status in ['submitted', 'late']])
    
    completion_rate = round((completed / total_assignments) * 100, 1) if total_assignments > 0 else 0
    
    # Calculate average score
    scores = [s.score for s in submissions if s.score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    
    pending = total_assignments - completed
    
    recent = AssignmentSubmission.query.filter_by(student_id=student_id).order_by(
        AssignmentSubmission.submitted_at.desc()
    ).limit(5).all()
    
    return {
        'completion_rate': completion_rate,
        'avg_score': avg_score,
        'pending': pending,
        'recent': recent
    }

def calculate_assessment_stats(student_id):
    """Calculate quiz and exam averages"""
    from models import AssessmentResult, Assessment
    
    results = AssessmentResult.query.filter_by(student_id=student_id).all()
    
    quiz_scores = []
    exam_scores = []
    
    for result in results:
        assessment = Assessment.query.get(result.assessment_id)
        if assessment:
            if assessment.type == 'quiz':
                quiz_scores.append(result.percentage if result.percentage else result.score)
            elif assessment.type == 'exam':
                exam_scores.append(result.percentage if result.percentage else result.score)
    
    quiz_avg = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else 0
    exam_avg = round(sum(exam_scores) / len(exam_scores), 1) if exam_scores else 0
    
    recent = AssessmentResult.query.filter_by(student_id=student_id).order_by(
        AssessmentResult.id.desc()
    ).limit(5).all()
    
    return {
        'quiz_avg': quiz_avg,
        'exam_avg': exam_avg,
        'recent': recent
    }

def calculate_performance_trend(student_id):
    """Calculate overall performance trend"""
    from models import AssessmentResult
    
    results = AssessmentResult.query.filter_by(student_id=student_id).order_by(
        AssessmentResult.id.desc()
    ).limit(6).all()
    
    if len(results) < 6:
        return 'unknown'
    
    recent_3 = results[:3]
    previous_3 = results[3:6]
    
    recent_avg = sum(r.percentage or r.score or 0 for r in recent_3) / 3
    previous_avg = sum(r.percentage or r.score or 0 for r in previous_3) / 3
    
    if recent_avg > previous_avg + 5:
        return 'improving'
    elif recent_avg < previous_avg - 5:
        return 'declining'
    else:
        return 'stable'
