import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import MarksRecord, User, Student, Teacher, Course, AttendanceRecord
from app.schemas import AttendanceSummary


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def generate_student_id() -> str:
    """Generate a student ID using the standard prefix."""
    return generate_id("STU-")


def compute_marks_summary(marks_record: MarksRecord) -> dict:
    """Compute marks summary with percentage and grade."""
    if not marks_record:
        return {}
    
    assessments = marks_record.assessments or {}
    totals = marks_record.totals or {}
    
    obtained = (
        assessments.get("quiz", 0) +
        assessments.get("assignment", 0) +
        assessments.get("mid", 0) +
        assessments.get("final", 0)
    )
    
    total = (
        totals.get("quiz", 0) +
        totals.get("assignment", 0) +
        totals.get("mid", 0) +
        totals.get("final", 0)
    )
    
    percentage = int((obtained / total * 100)) if total > 0 else 0
    grade = grade_from_percentage(percentage)
    
    return {
        "obtained": obtained,
        "total": total,
        "percentage": percentage,
        "grade": grade
    }


def grade_from_percentage(percentage: int) -> str:
    """Convert percentage to letter grade."""
    if percentage >= 85:
        return "A"
    elif percentage >= 80:
        return "A-"
    elif percentage >= 75:
        return "B+"
    elif percentage >= 70:
        return "B"
    elif percentage >= 65:
        return "B-"
    elif percentage >= 60:
        return "C+"
    elif percentage >= 55:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"


def get_student_overview(student_id: str, db: Session) -> dict:
    """Get complete student overview including marks and attendance."""
    student = db.query(Student).filter(Student.id == student_id).first()
    
    # Get marks for this student
    marks_records = db.query(MarksRecord).filter(
        MarksRecord.student_id == student_id
    ).all()
    
    mark_rows = []
    for mark in marks_records:
        summary = compute_marks_summary(mark)
        mark_rows.append({
            "id": mark.id,
            "studentId": mark.student_id,
            "courseCode": mark.course_code,
            "classCode": mark.class_code,
            "assessments": mark.assessments,
            "totals": mark.totals,
            **summary
        })
    
    # Get attendance summary for this student
    attendance_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student_id
    ).all()
    
    attendance_by_course = {}
    for record in attendance_records:
        key = f"{record.student_id}-{record.course_code}"
        if key not in attendance_by_course:
            attendance_by_course[key] = {
                "studentId": record.student_id,
                "courseCode": record.course_code,
                "classCode": record.class_code,
                "present": 0,
                "total": 0
            }
        
        attendance_by_course[key]["total"] += 1
        if record.status == "Present":
            attendance_by_course[key]["present"] += 1
    
    attendance_rows = []
    for item in attendance_by_course.values():
        percentage = int((item["present"] / item["total"] * 100)) if item["total"] > 0 else 0
        item["absent"] = item["total"] - item["present"]
        item["percentage"] = percentage
        attendance_rows.append(item)
    
    return {
        "student": student,
        "mark_rows": mark_rows,
        "attendance_rows": attendance_rows
    }


def get_teacher_by_id(teacher_id: str, db: Session) -> Teacher:
    """Get teacher by ID."""
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()
