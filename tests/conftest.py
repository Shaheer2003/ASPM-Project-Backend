"""
Pytest Configuration and Fixtures

Provides reusable fixtures for testing all endpoints and database operations.
Includes test database setup, mock user authentication, and helper functions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.main import app
from app.database import Base, get_db
from app.models import (
    User, Student, Teacher, Course, AttendanceRecord, MarksRecord,
    UserRole, UserStatus, AttendanceStatus, Session as SessionEnum
)
from app.auth.utils import get_password_hash, create_access_token
from app.config import get_settings

# ==================== Database Fixtures ====================

@pytest.fixture(scope="function")
def test_db():
    """
    Create an in-memory SQLite test database.
    
    Ensures complete isolation between tests by creating a fresh database
    for each test function.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal()
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def override_get_db(test_db):
    """
    Override get_db dependency with test database.
    
    Replaces the real database dependency with our in-memory test database
    for all API route tests.
    """
    def _override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db):
    """
    FastAPI test client with overridden database.
    
    Provides a test client that can make requests to the endpoints
    using the in-memory test database.
    """
    return TestClient(app)


# ==================== User/Authentication Fixtures ====================

@pytest.fixture
def admin_user(test_db):
    """
    Create and return a test admin user.
    
    The admin user has full permissions across all endpoints.
    Password: admin123
    """
    admin = User(
        username="admin",
        email="admin@test.com",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


@pytest.fixture
def teacher_user(test_db):
    """
    Create and return a test teacher user.
    
    Teacher can manage attendance, marks, and view student profiles.
    Password: teacher123
    """
    teacher = User(
        username="teacher1",
        email="teacher1@test.com",
        password_hash=get_password_hash("teacher123"),
        role=UserRole.TEACHER,
        status=UserStatus.ACTIVE
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    
    teacher_record = Teacher(
        user_id=teacher.id,
        assigned_classes=["Class-A", "Class-B"]
    )
    test_db.add(teacher_record)
    test_db.commit()
    test_db.refresh(teacher_record)
    
    return teacher


@pytest.fixture
def student_user(test_db):
    """
    Create and return a test student user.
    
    Student can view attendance, marks, and personal profile.
    Password: student123
    """
    student = User(
        username="student1",
        email="student1@test.com",
        password_hash=get_password_hash("student123"),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE
    )
    test_db.add(student)
    test_db.commit()
    test_db.refresh(student)
    
    student_record = Student(
        user_id=student.id,
        class_code="Class-A",
        department="Computer Science",
        phone="9876543210",
        batch="2023"
    )
    test_db.add(student_record)
    test_db.commit()
    test_db.refresh(student_record)
    
    return student


# ==================== Authentication Token Fixtures ====================

@pytest.fixture
def admin_token(admin_user):
    """
    Create and return a valid JWT token for admin user.
    
    Token expires after settings.access_token_expire_minutes.
    """
    settings = get_settings()
    return create_access_token(
        data={"sub": admin_user.username, "role": admin_user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )


@pytest.fixture
def teacher_token(teacher_user):
    """Create and return a valid JWT token for teacher user."""
    settings = get_settings()
    return create_access_token(
        data={"sub": teacher_user.username, "role": teacher_user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )


@pytest.fixture
def student_token(student_user):
    """Create and return a valid JWT token for student user."""
    settings = get_settings()
    return create_access_token(
        data={"sub": student_user.username, "role": student_user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )


@pytest.fixture
def auth_headers(admin_token):
    """
    Create authorization headers with admin token.
    
    Returns a dict with Authorization header that can be passed to client requests.
    """
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def teacher_auth_headers(teacher_token):
    """Create authorization headers with teacher token."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def student_auth_headers(student_token):
    """Create authorization headers with student token."""
    return {"Authorization": f"Bearer {student_token}"}


# ==================== Data Fixtures ====================

@pytest.fixture
def test_course(test_db):
    """Create and return a test course."""
    course = Course(
        code="CS101",
        name="Introduction to Computer Science",
        class_code="Class-A"
    )
    test_db.add(course)
    test_db.commit()
    test_db.refresh(course)
    return course


@pytest.fixture
def test_attendance_record(test_db, student_user, teacher_user, test_course):
    """Create and return a test attendance record."""
    attendance = AttendanceRecord(
        student_id=student_user.id,
        class_code="Class-A",
        course_code="CS101",
        date=datetime.utcnow().date(),
        session=SessionEnum.MORNING,
        status=AttendanceStatus.PRESENT,
        teacher_id=teacher_user.id
    )
    test_db.add(attendance)
    test_db.commit()
    test_db.refresh(attendance)
    return attendance


@pytest.fixture
def test_marks_record(test_db, student_user, teacher_user, test_course):
    """Create and return a test marks record."""
    marks = MarksRecord(
        student_id=student_user.id,
        course_code="CS101",
        class_code="Class-A",
        teacher_id=teacher_user.id,
        assessments={"assignment1": 20, "assignment2": 18, "project": 25},
        total_marks=90,
        percentage=90.0,
        grade="A"
    )
    test_db.add(marks)
    test_db.commit()
    test_db.refresh(marks)
    return marks


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_email_service():
    """Mock email service for password reset testing."""
    with patch('app.routes.auth.send_email') as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_jwt_decode():
    """Mock JWT decode for token validation testing."""
    with patch('app.auth.utils.jwt.decode') as mock:
        yield mock


# ==================== Utility Fixtures ====================

@pytest.fixture
def sample_student_data():
    """Provide sample student registration data."""
    return {
        "username": "newstudent",
        "email": "newstudent@test.com",
        "password": "NewStudent@123",
        "class_code": "Class-A",
        "department": "Computer Science",
        "phone": "9876543210",
        "batch": "2023"
    }


@pytest.fixture
def sample_course_data():
    """Provide sample course creation data."""
    return {
        "code": "CS102",
        "name": "Data Structures",
        "class_code": "Class-B"
    }


@pytest.fixture
def sample_attendance_data():
    """Provide sample attendance marking data."""
    return {
        "class_code": "Class-A",
        "course_code": "CS101",
        "date": datetime.utcnow().date(),
        "session": "MORNING",
        "attendance": [
            {"student_id": 1, "status": "PRESENT"},
            {"student_id": 2, "status": "ABSENT"}
        ]
    }
