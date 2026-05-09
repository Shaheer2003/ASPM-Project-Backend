from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import User, Course, Student, AttendanceRecord, MarksRecord
from app.auth.dependencies import get_current_user
from app.routes.utils import compute_marks_summary

router = APIRouter(prefix="/api/shared", tags=["shared"])


@router.get("/courses", response_model=List[Dict[str, str]])
async def get_courses(db: Session = Depends(get_db)):
    """Get all courses."""
    courses = db.query(Course).all()
    return [
        {
            "code": c.code,
            "name": c.name,
            "classCode": c.class_code
        }
        for c in courses
    ]


@router.get("/students", response_model=List[Dict[str, Any]])
async def get_all_students(
    db: Session = Depends(get_db)
):
    """Get all students (accessible by all authenticated users)."""
    students = db.query(Student).all()
    return [
        {
            "id": s.id,
            "name": s.user.name if s.user else "",
            "email": s.user.email if s.user else "",
            "classCode": s.class_code,
            "department": s.department,
            "phone": s.phone,
            "batch": s.batch
        }
        for s in students
    ]


@router.get("/attendance-summary", response_model=Dict[str, Any])
async def get_attendance_summary(
    db: Session = Depends(get_db)
):
    """Get attendance summary by student and course."""
    records = db.query(AttendanceRecord).all()
    
    summary_map = {}
    for record in records:
        key = f"{record.student_id}-{record.course_code}"
        if key not in summary_map:
            summary_map[key] = {
                "student_id": record.student_id,
                "course_code": record.course_code,
                "class_code": record.class_code,
                "present": 0,
                "total": 0
            }
        
        summary_map[key]["total"] += 1
        if record.status == "Present":
            summary_map[key]["present"] += 1
    
    summaries = []
    for item in summary_map.values():
        percentage = int((item["present"] / item["total"] * 100)) if item["total"] > 0 else 0
        item["absent"] = item["total"] - item["present"]
        item["percentage"] = percentage
        summaries.append(item)
    
    return {
        "summaries": summaries,
        "total_records": len(records)
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
