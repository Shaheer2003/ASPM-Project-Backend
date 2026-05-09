from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ Auth Schemas ============

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    ok: bool
    access_token: str
    token_type: str
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    ok: bool
    token: Optional[str] = None
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, alias="new_password")

    model_config = ConfigDict(populate_by_name=True)


class ResetPasswordResponse(BaseModel):
    ok: bool
    message: str


# ============ User Schemas ============

class UserBase(BaseModel):
    username: str
    email: EmailStr
    name: Optional[str] = None
    role: str
    status: str = "Active"
    department: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Student Schemas ============

class StudentBase(BaseModel):
    name: str
    email: EmailStr
    class_code: str
    department: str
    phone: Optional[str] = None
    batch: str = "2022-2026"


class StudentCreate(StudentBase):
    student_id: str


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    class_code: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None


class StudentResponse(StudentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Teacher Schemas ============

class TeacherBase(BaseModel):
    name: str
    email: EmailStr
    department: str
    assigned_classes: Optional[List[str]] = None


class TeacherCreate(TeacherBase):
    employee_id: str


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    assigned_classes: Optional[List[str]] = None


class TeacherResponse(TeacherBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Course Schemas ============

class CourseCreate(BaseModel):
    code: str
    name: str
    class_code: str


class CourseResponse(BaseModel):
    code: str
    name: str
    class_code: str

    class Config:
        from_attributes = True


# ============ Attendance Schemas ============

class AttendanceEntry(BaseModel):
    student_id: str
    status: str  # "Present" or "Absent"


class MarkAttendanceRequest(BaseModel):
    class_code: str
    date: str  # Format: YYYY-MM-DD
    session: str  # "Morning" or "Evening"
    entries: List[AttendanceEntry]


class UpdateAttendanceRequest(BaseModel):
    status: str  # "Present" or "Absent"


class AttendanceRecordResponse(BaseModel):
    id: str
    student_id: str
    class_code: str
    course_code: str
    date: str
    session: str
    status: str
    teacher_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceSummary(BaseModel):
    student_id: str
    course_code: str
    class_code: str
    present: int
    absent: int
    total: int
    percentage: float


# ============ Marks Schemas ============

class MarksRow(BaseModel):
    student_id: str
    obtained: float


class UpsertMarksRequest(BaseModel):
    class_code: str
    course_code: str
    assessment: str  # "Quiz 1", "Assignment 1", "Mid Term", "Final"
    rows: List[MarksRow]


class AssessmentBreakdown(BaseModel):
    obtained: float
    total: float
    percentage: float


class MarksRecordResponse(BaseModel):
    id: str
    student_id: str
    course_code: str
    class_code: str
    assessments: Dict[str, float]
    totals: Dict[str, float]
    obtained: Optional[float] = None
    total: Optional[float] = None
    percentage: Optional[float] = None
    grade: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Dashboard/Report Schemas ============

class StudentOverviewResponse(BaseModel):
    student: Optional[StudentResponse] = None
    mark_rows: List[Dict[str, Any]] = []
    attendance_rows: List[AttendanceSummary] = []


class GenericResponse(BaseModel):
    ok: bool
    message: str
    data: Optional[Dict[str, Any]] = None
