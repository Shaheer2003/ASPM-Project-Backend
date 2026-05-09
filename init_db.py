"""
Database initialization script to seed initial data.
Run this after creating the database to populate seed data.
"""

import os
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, Student, Teacher, Course, UserRole, UserStatus
from app.auth.utils import hash_password


def init_db():
    """Initialize database with seed data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if data already exists
    try:
        if db.query(User).first():
            print("Database already initialized with seed data.")
            db.close()
            return
    except OperationalError:
        db.close()
        if os.path.exists("aspm.db"):
            engine.dispose()
            os.remove("aspm.db")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
    
    # Create courses
    courses_data = [
        {"code": "SE303", "name": "Software Project Management", "class_code": "SE303-A"},
        {"code": "CS301", "name": "Database Systems", "class_code": "CS301-B"},
        {"code": "CS305", "name": "Operating Systems", "class_code": "CS305-A"},
    ]
    
    courses = []
    for course_data in courses_data:
        course = Course(**course_data)
        db.add(course)
        courses.append(course)
    
    db.flush()
    
    # Create admin user
    admin = User(
        id="ADM-001",
        username="admin",
        email="admin@miniflex.edu",
        name="System Admin",
        password=hash_password("admin123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        department="Administration"
    )
    db.add(admin)
    db.flush()
    
    # Create teachers
    teachers_data = [
        {"id": "EMP-1203", "username": "teacher", "name": "Dr. Ayesha Malik", "email": "ayesha.malik@miniflex.edu", "assigned_classes": ["SE303-A", "CS301-B", "CS305-A"]},
        {"id": "EMP-2204", "username": "teacher2", "name": "Sir Umer Khalid", "email": "umer.khalid@miniflex.edu", "assigned_classes": ["CS301-B"]},
        {"id": "EMP-3305", "username": "nida", "name": "Ma'am Nida Shaikh", "email": "nida.shaikh@miniflex.edu", "assigned_classes": ["CS305-A"]},
    ]
    
    for teacher_data in teachers_data:
        assigned_classes = teacher_data.pop("assigned_classes", [])
        user = User(
            password=hash_password("teacher123"),
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE,
            department="Computer Science",
            **teacher_data
        )
        db.add(user)
        db.flush()
        
        teacher = Teacher(id=user.id, assigned_classes=assigned_classes)
        db.add(teacher)
    
    db.flush()
    
    # Create students
    students_data = [
        {"id": "22K-4169", "username": "22k-4169", "name": "Tameema Rehman", "email": "tameema.rehman@miniflex.edu", "class_code": "SE303-A", "department": "Computer Science", "phone": "+92 300 1234567", "batch": "2022-2026"},
        {"id": "22K-4389", "username": "22k-4389", "name": "Shaheer Mumtaz", "email": "shaheer.mumtaz@miniflex.edu", "class_code": "SE303-A", "department": "Computer Science", "phone": "+92 300 2234567", "batch": "2022-2026"},
        {"id": "22K-4396", "username": "22k-4396", "name": "Ahmed Yoshay", "email": "ahmed.yoshay@miniflex.edu", "class_code": "CS301-B", "department": "Computer Science", "phone": "+92 300 3234567", "batch": "2022-2026"},
        {"id": "22L-6754", "username": "22l-6754", "name": "Taha Tahir", "email": "taha.tahir@miniflex.edu", "class_code": "CS305-A", "department": "Software Engineering", "phone": "+92 300 4234567", "batch": "2022-2026"},
        {"id": "22K-4200", "username": "22k-4200", "name": "Ayesha Tariq", "email": "ayesha.tariq@miniflex.edu", "class_code": "CS305-A", "department": "Computer Science", "phone": "+92 300 5234567", "batch": "2022-2026"},
    ]
    
    for student_data in students_data:
        class_code = student_data.pop("class_code")
        department = student_data.pop("department")
        phone = student_data.pop("phone")
        batch = student_data.pop("batch")
        
        user = User(
            password=hash_password("student123"),
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            department=department,
            **student_data
        )
        db.add(user)
        db.flush()
        
        student = Student(
            id=user.id,
            class_code=class_code,
            department=department,
            phone=phone,
            batch=batch
        )
        db.add(student)
    
    db.commit()
    db.close()
    
    print("Database initialized successfully with seed data!")
    print("\nTest Credentials:")
    print("Admin: admin / admin123")
    print("Teacher: teacher / teacher123")
    print("Student: 22k-4169 / student123")


if __name__ == "__main__":
    init_db()
