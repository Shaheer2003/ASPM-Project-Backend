from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import User, Student, AttendanceRecord, MarksRecord, Course
from app.auth.dependencies import get_current_user, require_role
from app.routes.utils import compute_marks_summary, get_student_overview

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/profile", response_model=Dict[str, Any])
async def get_student_profile(
    current_user: User = Depends(require_role("Student")),
    db: Session = Depends(get_db)
):
    """Get current student's profile."""
    student = db.query(Student).filter(Student.id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record not found."
        )
    
    overview = get_student_overview(current_user.id, db)
    
    return {
        "student": {
            "id": student.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": student.phone,
            "department": student.department,
            "batch": student.batch,
            "class_code": student.class_code
        },
        "marks": overview["mark_rows"],
        "attendance": overview["attendance_rows"]
    }


@router.get("/attendance", response_model=Dict[str, Any])
async def get_student_attendance(
    current_user: User = Depends(require_role("Student")),
    db: Session = Depends(get_db)
):
    """Get student's attendance records."""
    student = db.query(Student).filter(Student.id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )
    
    overview = get_student_overview(current_user.id, db)
    
    # Get courses
    courses = db.query(Course).all()
    
    # Get attendance by date
    attendance_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == current_user.id
    ).all()
    
    dated_rows = sorted(
        [
            {
                "id": r.id,
                "date": r.date,
                "courseCode": r.course_code,
                "session": r.session,
                "status": r.status
            }
            for r in attendance_records
        ],
        key=lambda x: x["date"],
        reverse=True
    )
    
    return {
        "courses": overview["attendance_rows"],
        "dated_records": dated_rows,
        "course_list": [{"code": c.code, "name": c.name} for c in courses]
    }


@router.get("/marks", response_model=Dict[str, Any])
async def get_student_marks(
    current_user: User = Depends(require_role("Student")),
    db: Session = Depends(get_db)
):
    """Get student's marks."""
    overview = get_student_overview(current_user.id, db)
    
    return {
        "marks": overview["mark_rows"],
        "courses": db.query(Course).all()
    }


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_student_dashboard(
    current_user: User = Depends(require_role("Student")),
    db: Session = Depends(get_db)
):
    """Get student dashboard data."""
    overview = get_student_overview(current_user.id, db)
    
    # Calculate averages
    averages = {}
    if overview["mark_rows"]:
        avg_marks = sum(m["percentage"] for m in overview["mark_rows"]) / len(overview["mark_rows"])
        averages["avg_marks"] = int(avg_marks)
    else:
        averages["avg_marks"] = 0
    
    if overview["attendance_rows"]:
        avg_attendance = sum(a["percentage"] for a in overview["attendance_rows"]) / len(overview["attendance_rows"])
        averages["avg_attendance"] = int(avg_attendance)
    else:
        averages["avg_attendance"] = 0
    
    return {
        "student": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        },
        "marks": overview["mark_rows"],
        "attendance": overview["attendance_rows"],
        "statistics": {
            "total_courses": len(overview["mark_rows"]),
            "average_attendance": averages["avg_attendance"],
            "average_marks": averages["avg_marks"],
            "cgpa": (averages["avg_marks"] / 25) if averages["avg_marks"] > 0 else 0
        }
    }


@router.get("/insights", response_model=Dict[str, Any])
async def get_performance_insights(
    current_user: User = Depends(require_role("Student")),
    db: Session = Depends(get_db)
):
    """Get student performance insights."""
    overview = get_student_overview(current_user.id, db)
    
    courses = db.query(Course).all()
    course_map = {c.code: c.name for c in courses}
    
    insights = []
    for mark in overview["mark_rows"]:
        insights.append({
            "courseCode": mark["courseCode"],
            "courseName": course_map.get(mark["courseCode"], "Unknown"),
            "percentage": mark["percentage"],
            "grade": mark["grade"]
        })
    
    return {
        "insights": insights,
        "total_courses": len(insights),
        "average_percentage": int(sum(i["percentage"] for i in insights) / len(insights)) if insights else 0
    }
