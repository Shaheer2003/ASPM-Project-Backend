from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, Student, Teacher, AttendanceRecord, MarksRecord, Course, AttendanceStatus, Session as SessionEnum
from app.schemas import (
    MarkAttendanceRequest, UpdateAttendanceRequest, GenericResponse,
    UpsertMarksRequest, AttendanceRecordResponse
)
from app.auth.dependencies import get_current_user, require_role
from app.routes.utils import generate_id, compute_marks_summary, get_teacher_by_id

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.post("/attendance", response_model=GenericResponse)
@router.post("/mark-attendance", response_model=GenericResponse)
async def mark_attendance(
    request: MarkAttendanceRequest,
    current_user: User = Depends(require_role("Teacher")),
    db: Session = Depends(get_db)
):
    """Mark attendance for a class."""
    # Get students in class
    students = db.query(Student).filter(Student.class_code == request.class_code).all()
    if not students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No students found for this class."
        )
    
    # Check for duplicates
    duplicate = []
    for entry in request.entries:
        exists = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == entry.student_id,
            AttendanceRecord.class_code == request.class_code,
            AttendanceRecord.date == request.date
        ).first()
        if exists:
            duplicate.append(entry.student_id)
    
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate entries prevented for: {', '.join(duplicate)}"
        )
    
    # Get course code
    course = db.query(Course).filter(Course.class_code == request.class_code).first()
    course_code = course.code if course else "GEN"
    
    # Create attendance records
    for entry in request.entries:
        record = AttendanceRecord(
            id=generate_id("ATT-"),
            student_id=entry.student_id,
            class_code=request.class_code,
            course_code=course_code,
            date=request.date,
            session=entry.status,
            status=entry.status,
            teacher_id=current_user.id
        )
        db.add(record)
    
    db.commit()
    
    return GenericResponse(
        ok=True,
        message="Attendance saved successfully."
    )


@router.put("/attendance/{record_id}", response_model=GenericResponse)
async def update_attendance(
    record_id: str,
    request: UpdateAttendanceRequest,
    current_user: User = Depends(require_role("Teacher")),
    db: Session = Depends(get_db)
):
    """Update an attendance record."""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found."
        )
    
    record.status = request.status
    db.add(record)
    db.commit()
    
    return GenericResponse(
        ok=True,
        message="Attendance updated successfully."
    )


@router.post("/marks", response_model=GenericResponse)
async def upsert_marks(
    request: UpsertMarksRequest,
    current_user: User = Depends(require_role("Teacher")),
    db: Session = Depends(get_db)
):
    """Update or create marks for class assessment."""
    # Map assessment names to keys
    assessment_map = {
        "Quiz 1": "quiz",
        "Assignment 1": "assignment",
        "Mid Term": "mid",
        "Final": "final"
    }
    
    assessment_key = assessment_map.get(request.assessment)
    if not assessment_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown assessment type."
        )
    
    # Validate marks
    for row in request.rows:
        if row.obtained < 0 or row.obtained > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Marks must be between 0 and 100."
            )
    
    # Update or create marks
    for row in request.rows:
        marks_record = db.query(MarksRecord).filter(
            MarksRecord.student_id == row.student_id,
            MarksRecord.course_code == request.course_code
        ).first()
        
        if marks_record:
            # Update existing
            if not marks_record.assessments:
                marks_record.assessments = {}
            marks_record.assessments[assessment_key] = row.obtained
        else:
            # Create new
            marks_record = MarksRecord(
                id=generate_id("MRK-"),
                student_id=row.student_id,
                course_code=request.course_code,
                class_code=request.class_code,
                teacher_id=current_user.id,
                assessments={assessment_key: row.obtained, "quiz": 0, "assignment": 0, "mid": 0, "final": 0},
                totals={"quiz": 10, "assignment": 15, "mid": 25, "final": 50}
            )
        
        db.add(marks_record)
    
    db.commit()
    
    return GenericResponse(
        ok=True,
        message="Marks updated successfully."
    )


@router.get("/students", response_model=List[dict])
async def get_class_students(
    class_code: str,
    current_user: User = Depends(require_role("Teacher")),
    db: Session = Depends(get_db)
):
    """Get students in a teacher's class."""
    teacher = get_teacher_by_id(current_user.id, db)
    if not teacher or class_code not in (teacher.assigned_classes or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this class."
        )
    
    students = db.query(Student).filter(Student.class_code == class_code).all()
    
    return [
        {
            "id": s.id,
            "name": s.user.name if s.user else "",
            "email": s.user.email if s.user else "",
            "class_code": s.class_code,
            "department": s.department
        }
        for s in students
    ]
