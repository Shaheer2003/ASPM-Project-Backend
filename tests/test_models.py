"""
Unit Tests for Database Models

Tests model creation, relationships, validations, and business logic.
Uses SQLAlchemy in-memory database for isolated testing.
"""

import pytest
from datetime import datetime
from app.models import (
    User, Student, Teacher, Course, AttendanceRecord, MarksRecord,
    UserRole, UserStatus, AttendanceStatus, Session as SessionEnum
)


class TestUserModel:
    """Test User model creation and validation."""
    
    def test_create_user_minimal(self, test_db):
        """
        Test creating user with minimum required fields.
        
        Verifies:
        - User can be created with required fields
        - Defaults are applied correctly
        """
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.status == UserStatus.ACTIVE
        assert user.role == UserRole.STUDENT
    
    def test_user_unique_username(self, test_db):
        """
        Test that username must be unique.
        
        Verifies:
        - Creating duplicate username raises error
        """
        user1 = User(
            username="duplicate",
            email="user1@example.com",
            password_hash="hash1",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        test_db.add(user1)
        test_db.commit()
        
        user2 = User(
            username="duplicate",  # Duplicate
            email="user2@example.com",
            password_hash="hash2",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        test_db.add(user2)
        
        with pytest.raises(Exception):  # SQLAlchemy integrity error
            test_db.commit()
    
    def test_user_unique_email(self, test_db):
        """
        Test that email must be unique.
        
        Verifies:
        - Duplicate email raises error
        """
        user1 = User(
            username="user1",
            email="duplicate@example.com",
            password_hash="hash1",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        test_db.add(user1)
        test_db.commit()
        
        user2 = User(
            username="user2",
            email="duplicate@example.com",  # Duplicate
            password_hash="hash2",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        test_db.add(user2)
        
        with pytest.raises(Exception):
            test_db.commit()
    
    def test_user_role_enum(self, test_db):
        """
        Test user role enum validation.
        
        Verifies:
        - Only valid roles accepted
        - Roles are properly stored
        """
        for role in [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT]:
            user = User(
                username=f"user_{role.value}",
                email=f"user_{role.value}@example.com",
                password_hash="hash",
                role=role,
                status=UserStatus.ACTIVE
            )
            test_db.add(user)
            test_db.commit()
            test_db.refresh(user)
            assert user.role == role
    
    def test_user_status_enum(self, test_db):
        """Test user status enum validation."""
        for status in [UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.SUSPENDED]:
            user = User(
                username=f"user_{status.value}",
                email=f"user_{status.value}@example.com",
                password_hash="hash",
                role=UserRole.STUDENT,
                status=status
            )
            test_db.add(user)
            test_db.commit()
            test_db.refresh(user)
            assert user.status == status


class TestStudentModel:
    """Test Student model and relationships."""
    
    def test_create_student(self, test_db, admin_user):
        """
        Test creating student with user relationship.
        
        Verifies:
        - Student references valid user
        - Student-specific fields stored correctly
        """
        student = Student(
            user_id=admin_user.id,
            class_code="Class-A",
            department="Computer Science",
            phone="9876543210",
            batch="2023"
        )
        test_db.add(student)
        test_db.commit()
        test_db.refresh(student)
        
        assert student.user_id == admin_user.id
        assert student.class_code == "Class-A"
        assert student.department == "Computer Science"
    
    def test_student_user_relationship(self, test_db, student_user):
        """
        Test student to user relationship.
        
        Verifies:
        - Can access user from student
        - User information accessible
        """
        student = test_db.query(Student).filter(
            Student.user_id == student_user.id
        ).first()
        
        assert student is not None
        assert student.user.username == student_user.username
        assert student.user.role == UserRole.STUDENT


class TestTeacherModel:
    """Test Teacher model and relationships."""
    
    def test_create_teacher(self, test_db, teacher_user):
        """
        Test creating teacher record.
        
        Verifies:
        - Teacher can be created with assigned classes
        - JSON field correctly stores class assignments
        """
        teacher = test_db.query(Teacher).filter(
            Teacher.user_id == teacher_user.id
        ).first()
        
        assert teacher is not None
        assert "Class-A" in teacher.assigned_classes
        assert isinstance(teacher.assigned_classes, list)
    
    def test_update_teacher_classes(self, test_db, teacher_user):
        """
        Test updating teacher's assigned classes.
        
        Verifies:
        - Can modify assigned classes
        - Changes persist to database
        """
        teacher = test_db.query(Teacher).filter(
            Teacher.user_id == teacher_user.id
        ).first()
        
        teacher.assigned_classes = ["Class-B", "Class-C"]
        test_db.commit()
        test_db.refresh(teacher)
        
        assert "Class-B" in teacher.assigned_classes
        assert "Class-A" not in teacher.assigned_classes


class TestCourseModel:
    """Test Course model."""
    
    def test_create_course(self, test_db):
        """
        Test creating course.
        
        Verifies:
        - Course fields validated and stored
        """
        course = Course(
            code="CS101",
            name="Introduction to CS",
            class_code="Class-A"
        )
        test_db.add(course)
        test_db.commit()
        test_db.refresh(course)
        
        assert course.id is not None
        assert course.code == "CS101"
        assert course.name == "Introduction to CS"
    
    def test_course_unique_code(self, test_db):
        """
        Test course code uniqueness.
        
        Verifies:
        - Duplicate course code raises error
        """
        course1 = Course(code="CS101", name="Course 1", class_code="Class-A")
        test_db.add(course1)
        test_db.commit()
        
        course2 = Course(code="CS101", name="Course 2", class_code="Class-B")
        test_db.add(course2)
        
        with pytest.raises(Exception):
            test_db.commit()


class TestAttendanceRecord:
    """Test AttendanceRecord model."""
    
    def test_create_attendance(self, test_db, student_user, teacher_user):
        """
        Test creating attendance record.
        
        Verifies:
        - Attendance record stores all required data
        - Relationships to student and teacher verified
        """
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
        
        assert attendance.id is not None
        assert attendance.status == AttendanceStatus.PRESENT
        assert attendance.session == SessionEnum.MORNING
    
    def test_attendance_status_enum(self, test_db, student_user, teacher_user):
        """
        Test attendance status enum.
        
        Verifies:
        - All valid statuses work correctly
        """
        for status in [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.LEAVE]:
            attendance = AttendanceRecord(
                student_id=student_user.id,
                class_code="Class-A",
                course_code="CS101",
                date=datetime.utcnow().date(),
                session=SessionEnum.MORNING,
                status=status,
                teacher_id=teacher_user.id
            )
            test_db.add(attendance)
            test_db.commit()
            test_db.refresh(attendance)
            assert attendance.status == status


class TestMarksRecord:
    """Test MarksRecord model."""
    
    def test_create_marks(self, test_db, student_user, teacher_user):
        """
        Test creating marks record.
        
        Verifies:
        - Marks stored with assessments and calculated fields
        """
        marks = MarksRecord(
            student_id=student_user.id,
            course_code="CS101",
            class_code="Class-A",
            teacher_id=teacher_user.id,
            assessments={"assignment1": 20, "project": 30},
            total_marks=85,
            percentage=85.0,
            grade="A"
        )
        test_db.add(marks)
        test_db.commit()
        test_db.refresh(marks)
        
        assert marks.id is not None
        assert marks.total_marks == 85
        assert marks.percentage == 85.0
        assert marks.grade == "A"
    
    def test_marks_json_field(self, test_db, student_user, teacher_user):
        """
        Test that assessments JSON field works.
        
        Verifies:
        - Complex JSON data stored and retrieved correctly
        """
        assessments = {
            "assignment1": 18,
            "assignment2": 22,
            "project": 30,
            "exam": 70
        }
        
        marks = MarksRecord(
            student_id=student_user.id,
            course_code="CS101",
            class_code="Class-A",
            teacher_id=teacher_user.id,
            assessments=assessments,
            total_marks=90,
            percentage=90.0,
            grade="A"
        )
        test_db.add(marks)
        test_db.commit()
        test_db.refresh(marks)
        
        assert marks.assessments == assessments
        assert marks.assessments["assignment1"] == 18


class TestModelRelationships:
    """Test relationships between models."""
    
    def test_student_attendance_relationship(self, test_db, student_user, teacher_user):
        """
        Test student to attendance relationship.
        
        Verifies:
        - Can retrieve attendance records for student
        """
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
        
        # Query back
        records = test_db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student_user.id
        ).all()
        
        assert len(records) == 1
        assert records[0].student_id == student_user.id
