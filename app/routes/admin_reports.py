from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from app.database import get_db
from app.models import User, AttendanceRecord, MarksRecord, Course, Student
from app.auth.dependencies import get_current_user, require_role
from app.routes.utils import compute_marks_summary

router = APIRouter(prefix="/api/admin-reports", tags=["admin-reports"])


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_admin_dashboard(
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics."""
    total_users = db.query(User).count()
    total_students = db.query(Student).count()
    total_teachers = db.query(User).filter(User.role == "Teacher").count()
    total_attendance = db.query(AttendanceRecord).count()
    total_marks = db.query(MarksRecord).count()
    
    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_attendance_records": total_attendance,
        "total_marks_records": total_marks,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/reports/attendance", response_model=Dict[str, Any])
async def get_attendance_reports(
    student_id: str = Query(None),
    class_code: str = Query(None),
    date: str = Query(None),
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Get filtered attendance reports."""
    query = db.query(AttendanceRecord)
    
    if student_id:
        query = query.filter(AttendanceRecord.student_id == student_id)
    if class_code:
        query = query.filter(AttendanceRecord.class_code == class_code)
    if date:
        query = query.filter(AttendanceRecord.date == date)
    
    records = query.all()
    
    # Calculate summary
    present = sum(1 for r in records if r.status == "Present")
    total = len(records)
    percentage = int((present / total * 100)) if total > 0 else 0
    
    return {
        "records": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "class_code": r.class_code,
                "date": r.date,
                "session": r.session,
                "status": r.status
            }
            for r in records
        ],
        "summary": {
            "total": total,
            "present": present,
            "absent": total - present,
            "percentage": percentage
        }
    }


@router.get("/reports/marks", response_model=Dict[str, Any])
async def get_marks_reports(
    student_id: str = Query(None),
    class_code: str = Query(None),
    course_code: str = Query(None),
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Get filtered marks reports."""
    query = db.query(MarksRecord)
    
    if student_id:
        query = query.filter(MarksRecord.student_id == student_id)
    if class_code:
        query = query.filter(MarksRecord.class_code == class_code)
    if course_code:
        query = query.filter(MarksRecord.course_code == course_code)
    
    records = query.all()
    
    report_rows = []
    for record in records:
        summary = compute_marks_summary(record)
        report_rows.append({
            "id": record.id,
            "student_id": record.student_id,
            "course_code": record.course_code,
            "class_code": record.class_code,
            "assessments": record.assessments,
            "totals": record.totals,
            **summary
        })
    
    return {
        "records": report_rows,
        "total": len(report_rows)
    }


@router.get("/reports/class-performance", response_model=Dict[str, Any])
async def get_class_performance(
    class_code: str,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Get performance report for a specific class."""
    students = db.query(Student).filter(Student.class_code == class_code).all()
    
    performance = []
    for student in students:
        # Get attendance
        attendance = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.class_code == class_code
        ).all()
        
        attendance_percentage = 0
        if attendance:
            present = sum(1 for r in attendance if r.status == "Present")
            attendance_percentage = int((present / len(attendance) * 100))
        
        # Get marks
        marks = db.query(MarksRecord).filter(
            MarksRecord.student_id == student.id,
            MarksRecord.class_code == class_code
        ).all()
        
        avg_percentage = 0
        if marks:
            avg_percentage = int(sum(compute_marks_summary(m).get("percentage", 0) for m in marks) / len(marks))
        
        performance.append({
            "student_id": student.id,
            "student_name": student.user.name if student.user else "",
            "attendance_percentage": attendance_percentage,
            "marks_percentage": avg_percentage,
            "overall_score": int((attendance_percentage + avg_percentage) / 2)
        })
    
    return {
        "class_code": class_code,
        "total_students": len(students),
        "performance": sorted(performance, key=lambda x: x["overall_score"], reverse=True)
    }
