"""
Database Models

Defines SQLAlchemy ORM models for all application entities.
Includes User, Student, Teacher, Course, Attendance, and Marks records.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, synonym
from datetime import datetime
import uuid
import enum
from app.database import Base


# ==================== Enum Definitions ====================

class UserRole(str, enum.Enum):
    """User role enumeration for access control."""
    ADMIN = "Admin"      # Administrative user with full permissions
    TEACHER = "Teacher"  # Teacher user who manages students and records
    STUDENT = "Student"  # Student user who views own profile and records


class UserStatus(str, enum.Enum):
    """User account status enumeration."""
    ACTIVE = "Active"        # User can login and use the system
    ARCHIVED = "Archived"    # User archived but data preserved
    INACTIVE = "Inactive"    # User disabled and cannot login
    SUSPENDED = "Suspended"  # Legacy status expected by tests


class AttendanceStatus(str, enum.Enum):
    """Attendance record status enumeration."""
    PRESENT = "Present"  # Student was present
    ABSENT = "Absent"    # Student was absent
    LEAVE = "Leave"      # Student had authorized leave


class Session(str, enum.Enum):
    """Class session enumeration."""
    MORNING = "Morning"      # Morning session (typically 9 AM - 12 PM)
    AFTERNOON = "Afternoon"  # Afternoon session (typically 2 PM - 5 PM)


# ==================== Core Models ====================

class User(Base):
    """
    User model - Core authentication and user management.
    
    Base model for all user types (Admin, Teacher, Student).
    Stores authentication credentials and user metadata.
    """
    __tablename__ = "users"

    # Primary key and authentication fields
    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex[:12])  # Unique user ID
    username = Column(String, unique=True, index=True)  # Unique username for login
    email = Column(String, unique=True, index=True)    # Unique email address
    name = Column(String)                               # Display name for the user
    department = Column(String, nullable=True)          # User department / faculty area
    password = Column(String)                            # Hashed password (bcrypt)
    password_hash = synonym('password')
    
    # User metadata
    role = Column(Enum(UserRole), default=UserRole.STUDENT)        # User role for access control
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)   # Account status
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)         # Account creation timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last update timestamp

    # Relationships for lazy loading related data
    student = relationship("Student", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)
    attendance_records = relationship("AttendanceRecord", back_populates="teacher", foreign_keys="AttendanceRecord.teacher_id")
    marks_records = relationship("MarksRecord", back_populates="teacher", foreign_keys="MarksRecord.teacher_id")
    password_resets = relationship("PasswordReset", back_populates="user")


class Student(Base):
    """
    Student model - Student-specific information.
    
    Extends User model with student-specific fields.
    Linked to User via foreign key (inheritance pattern).
    """
    __tablename__ = "students"

    # Foreign key to Users table (also primary key)
    id = Column(String, ForeignKey("users.id"), primary_key=True)
    user_id = synonym("id")
    
    # Student-specific fields
    class_code = Column(String, index=True)     # Assigned class/section (e.g., "Class-A")
    department = Column(String)                  # Department (e.g., "Computer Science")
    phone = Column(String, nullable=True)        # Student contact number
    batch = Column(String)                       # Batch year (e.g., "2023")
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="student", foreign_keys="AttendanceRecord.student_id")
    marks_records = relationship("MarksRecord", back_populates="student", foreign_keys="MarksRecord.student_id")


class Teacher(Base):
    """
    Teacher model - Teacher-specific information.
    
    Extends User model with teacher-specific fields.
    Stores list of classes assigned to teacher.
    """
    __tablename__ = "teachers"

    # Foreign key to Users table (also primary key)
    id = Column(String, ForeignKey("users.id"), primary_key=True)
    user_id = synonym("id")
    
    # Teacher-specific fields
    assigned_classes = Column(JSON, default=list)  # JSON array of class codes teacher teaches
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="teacher")


class Course(Base):
    """
    Course model - Course information and curriculum.
    
    Stores course metadata linked to specific classes.
    Used to organize attendance and marks records.
    """
    __tablename__ = "courses"

    # Course identifier fields
    code = Column(String, primary_key=True, index=True)      # Unique course code (e.g., "CS101")
    id = synonym("code")
    name = Column(String)                                     # Course name (e.g., "Intro to CS")
    class_code = Column(String, unique=True, index=True)     # Associated class code

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="course")
    marks_records = relationship("MarksRecord", back_populates="course")


# ==================== Academic Records ====================

class AttendanceRecord(Base):
    """
    Attendance Record - Student attendance tracking.
    
    Records daily attendance for each student in each course.
    Marked by teacher for each session (morning/afternoon).
    """
    __tablename__ = "attendance_records"

    # Primary key
    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex[:12])
    
    # Foreign keys
    student_id = Column(String, ForeignKey("students.id"), index=True)  # Which student
    course_code = Column(String, ForeignKey("courses.code"), index=True)  # Which course
    teacher_id = Column(String, ForeignKey("users.id"))                   # Who marked attendance
    
    # Attendance details
    class_code = Column(String)                    # Class/section code
    date = Column(String, index=True)             # Date in YYYY-MM-DD format
    session = Column(Enum(Session))                # Morning or afternoon session
    status = Column(Enum(AttendanceStatus))        # Present/Absent/Leave
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)  # When marked
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last update

    # Relationships
    student = relationship("Student", back_populates="attendance_records", foreign_keys=[student_id])
    teacher = relationship("User", back_populates="attendance_records", foreign_keys=[teacher_id])
    course = relationship("Course", back_populates="attendance_records")


class MarksRecord(Base):
    """
    Marks Record - Student academic grades.
    
    Stores all assessment scores for a student in a course.
    Includes individual assessment scores and calculated totals.
    """
    __tablename__ = "marks_records"

    # Primary key
    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex[:12])
    
    # Foreign keys
    student_id = Column(String, ForeignKey("students.id"), index=True)  # Which student
    course_code = Column(String, ForeignKey("courses.code"), index=True)  # Which course
    teacher_id = Column(String, ForeignKey("users.id"))                   # Who entered marks
    
    # Marks details
    class_code = Column(String)                    # Class/section code
    assessments = Column(JSON)                     # Assessment breakdown: {name: score}
    total_marks = Column(Integer, nullable=True)   # Total marks obtained
    percentage = Column(Integer, nullable=True)    # Calculated percentage (0-100)
    grade = Column(String, nullable=True)          # Calculated grade (A+, A, B, C, D, F)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)  # When entered
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last update

    # Relationships
    student = relationship("Student", back_populates="marks_records", foreign_keys=[student_id])
    course = relationship("Course", back_populates="marks_records")
    teacher = relationship("User", back_populates="marks_records", foreign_keys=[teacher_id])


# ==================== Utility Models ====================

class PasswordReset(Base):
    """
    Password Reset - Password recovery tokens.
    
    Stores temporary tokens for password reset functionality.
    Tokens are single-use and expire after time limit.
    """
    __tablename__ = "password_resets"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key and email
    user_id = Column(String, ForeignKey("users.id"), index=True)  # Which user
    email = Column(String, index=True)                            # Email requesting reset
    
    # Token details
    token = Column(String, unique=True, index=True)  # Secure random token
    token_hash = synonym("token")
    is_used = Column(Boolean, default=False)         # Whether token has been used
    
    # Timestamps for token lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)    # When token created
    expires_at = Column(DateTime, index=True)                  # When token expires

    # Relationships
    user = relationship("User", back_populates="password_resets")
