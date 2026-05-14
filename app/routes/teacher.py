from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models import User, Student, Teacher, AttendanceRecord, MarksRecord, Course, AttendanceStatus, Session as SessionEnum
from app.schemas import (
    MarkAttendanceRequest, UpdateAttendanceRequest, GenericResponse,
    UpsertMarksRequest, AttendanceRecordResponse
)
from app.auth.dependencies import get_current_user, require_role
from app.routes.utils import generate_id, compute_marks_summary, get_teacher_by_id, get_student_overview

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.get("/profile", response_model=Dict[str, Any])
async def get_teacher_profile(
    current_user: User = Depends(require_role("Teacher")),
    db: Session = Depends(get_db)
):
    """Get teacher profile and assigned classes."""
    teacher = get_teacher_by_id(current_user.id, db)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found."
        )

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "assigned_classes": teacher.assigned_classes or []
    }


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
            session=request.session,
            status=entry.status,
            teacher_id=current_user.id
        )
        db.add(record)
    
    db.commit()
    
    return GenericResponse(
        ok=True,
        message="Attendance saved successfully."
    )


@router.get("/attendance", response_model=Dict[str, Any])
async def list_attendance(
    class_code: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    current_user: User = Depends(require_role("Teacher")),
    db: Session = Depends(get_db)
):
    """List attendance records for the current teacher."""
    query = db.query(AttendanceRecord).filter(AttendanceRecord.teacher_id == current_user.id)

    if class_code:
        query = query.filter(AttendanceRecord.class_code == class_code)
    if date:
        query = query.filter(AttendanceRecord.date == date)

    records = query.all()
    return {
        "records": [
            {
                "id": record.id,
                "student_id": record.student_id,
                "class_code": record.class_code,
                "course_code": record.course_code,
                "date": record.date,
                "session": record.session,
                "status": record.status,
                "teacher_id": record.teacher_id
            }
            for record in records
        ]
    }


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


@router.get("/marks", response_model=Dict[str, Any])
async def get_marks(
    class_code: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    current_user: User = Depends(require_role("Teacher")),
    db: Session = Depends(get_db)
):
    """Get marks records for the current teacher."""
    query = db.query(MarksRecord).filter(MarksRecord.teacher_id == current_user.id)

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


@router.get("/student-overview", response_model=Dict[str, Any])
async def get_student_overview_for_teacher(
    student_id: str,
    current_user: User = Depends(require_role("Teacher")),
    db: Session = Depends(get_db)
):
    """Get overview for a student in the teacher's assigned classes."""
    teacher = get_teacher_by_id(current_user.id, db)
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )

    if teacher and student.class_code not in (teacher.assigned_classes or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this student."
        )

    overview = get_student_overview(student_id, db)

    return {
        "student": {
            "id": student.id,
            "name": student.user.name if student.user else "",
            "email": student.user.email if student.user else "",
            "phone": student.phone,
            "department": student.department,
            "batch": student.batch,
            "class_code": student.class_code
        },
        "mark_rows": overview["mark_rows"],
        "attendance_rows": overview["attendance_rows"]
    }
