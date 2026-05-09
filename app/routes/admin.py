from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Student, Teacher, AttendanceRecord, MarksRecord, UserRole, UserStatus
from app.schemas import (
    UserResponse, StudentResponse, TeacherResponse, GenericResponse,
    StudentCreate, StudentUpdate, TeacherCreate, TeacherUpdate
)
from app.auth.dependencies import get_current_user, require_role
from app.auth.utils import hash_password
from app.routes.utils import generate_id

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Get all users."""
    users = db.query(User).all()
    return users


@router.post("/students", response_model=GenericResponse)
@router.post("/register-student", response_model=GenericResponse)
async def register_student(
    request: StudentCreate,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Register a new student."""
    # Validate input
    if not request.name.strip() or not request.student_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please fill all required fields."
        )
    
    # Check for duplicate student ID
    existing = db.query(Student).filter(Student.id == request.student_id.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate student ID is not allowed."
        )
    
    # Create user account
    user = User(
        id=request.student_id.strip(),
        username=request.student_id.strip().lower(),
        password=hash_password("student123"),
        role=UserRole.STUDENT,
        name=request.name.strip(),
        email=request.email,
        status=UserStatus.ACTIVE,
        department=request.department.strip()
    )
    
    db.add(user)
    db.flush()
    
    # Create student record
    student = Student(
        id=request.student_id.strip(),
        class_code=request.class_code.strip(),
        department=request.department.strip(),
        phone=request.phone if hasattr(request, 'phone') else "-",
        batch=request.batch
    )
    
    db.add(student)
    db.commit()
    
    return GenericResponse(
        ok=True,
        message="Student record saved successfully."
    )


@router.post("/teachers", response_model=GenericResponse)
@router.post("/register-teacher", response_model=GenericResponse)
async def register_teacher(
    request: TeacherCreate,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Register a new teacher."""
    # Validate input
    if not request.name.strip() or not request.employee_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please fill all required fields."
        )
    
    # Check for duplicate employee ID
    existing = db.query(User).filter(User.id == request.employee_id.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate employee ID is not allowed."
        )
    
    # Create user account
    user = User(
        id=request.employee_id.strip(),
        username=request.employee_id.strip().lower(),
        password=hash_password("teacher123"),
        role=UserRole.TEACHER,
        name=request.name.strip(),
        email=request.email,
        status=UserStatus.ACTIVE,
        department=request.department.strip()
    )
    
    db.add(user)
    db.flush()
    
    # Create teacher record
    teacher = Teacher(
        id=request.employee_id.strip(),
        assigned_classes=request.assigned_classes or []
    )
    
    db.add(teacher)
    db.commit()
    
    return GenericResponse(
        ok=True,
        message="Teacher account saved successfully."
    )


@router.put("/students/{student_id}", response_model=GenericResponse)
async def update_student(
    student_id: str,
    request: StudentUpdate,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Update student information."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )
    
    # Update student record
    if request.name:
        student.name = request.name.strip()
    if request.email:
        student.email = request.email
    if request.class_code:
        student.class_code = request.class_code.strip()
    if request.department:
        student.department = request.department.strip()
    if request.phone:
        student.phone = request.phone.strip()
    
    # Update user record
    user = db.query(User).filter(User.id == student_id).first()
    if user:
        if request.name:
            user.name = request.name.strip()
        if request.email:
            user.email = request.email
    
    db.add(student)
    if user:
        db.add(user)
    db.commit()
    
    return GenericResponse(
        ok=True,
        message="Student record updated successfully."
    )


@router.delete("/students/{student_id}", response_model=GenericResponse)
async def delete_or_archive_student(
    student_id: str,
    mode: str = "archive",
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Delete or archive a student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )
    
    if mode == "delete":
        # Delete all related records
        db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id).delete()
        db.query(MarksRecord).filter(MarksRecord.student_id == student_id).delete()
        db.query(Student).filter(Student.id == student_id).delete()
        db.query(User).filter(User.id == student_id).delete()
        db.commit()
        return GenericResponse(
            ok=True,
            message="Student record deleted successfully."
        )
    else:
        # Archive user
        user = db.query(User).filter(User.id == student_id).first()
        if user:
            user.status = UserStatus.ARCHIVED
            db.add(user)
        db.commit()
        return GenericResponse(
            ok=True,
            message="Student record archived successfully."
        )


@router.post("/users/{user_id}/role", response_model=GenericResponse)
async def assign_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Assign or change a user's role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    user.role = role
    db.add(user)
    db.commit()
    
    return GenericResponse(
        ok=True,
        message="User role updated successfully."
    )
