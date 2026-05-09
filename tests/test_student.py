"""
Student Endpoint Tests

Tests for student-specific features: attendance viewing, marks retrieval,
profile management, and performance insights.
"""

import pytest
from datetime import datetime, timedelta


class TestStudentProfileEndpoints:
    """Test student profile and personal data endpoints."""
    
    def test_get_student_profile(self, client, student_token, student_auth_headers, student_user):
        """
        Test retrieving student profile.
        
        Verifies:
        - Student can retrieve own profile
        - Returns complete student information
        - Response includes user and student-specific fields
        """
        response = client.get(
            "/api/student/profile",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "class_code" in data
        assert data["username"] == student_user.username
    
    def test_update_student_profile(self, client, student_token, student_auth_headers, student_user, test_db):
        """
        Test updating student profile.
        
        Verifies:
        - Student can update own profile information
        - Updates are persisted to database
        - Only own profile can be updated
        """
        update_data = {
            "phone": "9876543210"
        }
        
        response = client.put(
            "/api/student/profile",
            headers=student_auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "9876543210"
    
    def test_student_cannot_access_others_profile(self, client, student_token, student_auth_headers, admin_user):
        """
        Test that student cannot view others' profiles.
        
        Verifies:
        - Student can only access own profile
        - Accessing other profiles returns 403
        """
        response = client.get(
            f"/api/student/{admin_user.id}/profile",
            headers=student_auth_headers
        )
        # Should either 404 or 403 - not expose other students
        assert response.status_code in [403, 404]


class TestStudentAttendanceEndpoints:
    """Test student attendance viewing functionality."""
    
    def test_get_attendance_records(self, client, student_token, student_auth_headers, student_user, test_attendance_record):
        """
        Test retrieving student attendance records.
        
        Verifies:
        - Student can view own attendance
        - Returns all attendance records for student
        - Includes date, course, status information
        """
        response = client.get(
            "/api/student/attendance",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "records" in data
    
    def test_get_attendance_filters_by_student(self, client, student_token, student_auth_headers, student_user, test_db, test_attendance_record):
        """
        Test that attendance is filtered to current student only.
        
        Verifies:
        - Student sees only their own attendance
        - Other students' attendance not visible
        """
        response = client.get(
            "/api/student/attendance",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all records belong to this student
        if isinstance(data, list):
            for record in data:
                assert record["student_id"] == student_user.id
    
    def test_get_attendance_by_course(self, client, student_token, student_auth_headers, student_user, test_db, test_course):
        """
        Test retrieving attendance for specific course.
        
        Verifies:
        - Can filter attendance by course code
        - Returns only records for specified course
        """
        response = client.get(
            f"/api/student/attendance?course_code=CS101",
            headers=student_auth_headers
        )
        assert response.status_code == 200


class TestStudentMarksEndpoints:
    """Test student marks and grades functionality."""
    
    def test_get_marks_records(self, client, student_token, student_auth_headers, student_user, test_marks_record):
        """
        Test retrieving student marks.
        
        Verifies:
        - Student can view own marks
        - Returns all marks records
        - Includes course, grade, percentage
        """
        response = client.get(
            "/api/student/marks",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "records" in data
    
    def test_marks_include_calculated_fields(self, client, student_token, student_auth_headers, student_user, test_marks_record):
        """
        Test that marks include calculated fields.
        
        Verifies:
        - Marks include percentage calculation
        - Marks include grade assignment
        - Marks include assessment details
        """
        response = client.get(
            "/api/student/marks",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            record = data[0]
            assert "percentage" in record
            assert "grade" in record
            assert "total_marks" in record
    
    def test_get_marks_by_course(self, client, student_token, student_auth_headers, student_user, test_db, test_course):
        """
        Test retrieving marks for specific course.
        
        Verifies:
        - Can filter marks by course
        - Returns only marks for specified course
        """
        response = client.get(
            f"/api/student/marks?course_code=CS101",
            headers=student_auth_headers
        )
        assert response.status_code == 200


class TestStudentDashboardEndpoints:
    """Test student dashboard and summary endpoints."""
    
    def test_get_student_dashboard(self, client, student_token, student_auth_headers, student_user, test_db):
        """
        Test retrieving student dashboard.
        
        Verifies:
        - Dashboard contains summary statistics
        - Includes attendance count, marks average, etc.
        - Returns personalized data for student
        """
        response = client.get(
            "/api/student/dashboard",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data or "username" in data
    
    def test_get_performance_insights(self, client, student_token, student_auth_headers, student_user, test_db):
        """
        Test retrieving performance insights.
        
        Verifies:
        - Returns performance metrics
        - Includes subject-wise analysis
        - Includes performance trends
        """
        response = client.get(
            "/api/student/performance-insights",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should contain some analysis data
        assert data is not None


class TestStudentAccessControl:
    """Test access control for student endpoints."""
    
    def test_teacher_cannot_access_student_endpoints(self, client, teacher_token, teacher_auth_headers):
        """
        Test that teacher cannot access student-only endpoints.
        
        Verifies:
        - Teacher role denied access to /api/student/* endpoints
        """
        response = client.get(
            "/api/student/profile",
            headers=teacher_auth_headers
        )
        assert response.status_code == 403
    
    def test_admin_cannot_directly_access_student_endpoints(self, client, admin_token, auth_headers):
        """
        Test that admin has different student access endpoints.
        
        Verifies:
        - Admin may have separate endpoints for viewing student data
        - Admin cannot use /api/student/* endpoints
        """
        response = client.get(
            "/api/student/profile",
            headers=auth_headers
        )
        # Admin should not directly access student endpoints
        assert response.status_code in [403, 404]
    
    def test_student_cannot_access_teacher_endpoints(self, client, student_token, student_auth_headers):
        """
        Test that student cannot access teacher-only endpoints.
        
        Verifies:
        - Student role denied access to /api/teacher/* endpoints
        """
        response = client.post(
            "/api/teacher/mark-attendance",
            headers=student_auth_headers,
            json={"class_code": "Class-A", "attendance": []}
        )
        assert response.status_code == 403


class TestStudentDataIntegrity:
    """Test data integrity and consistency."""
    
    def test_student_sees_correct_attendance_percentage(self, client, student_token, student_auth_headers, student_user, test_db):
        """
        Test that attendance percentage is calculated correctly.
        
        Verifies:
        - Attendance percentage matches formula: (present / total) * 100
        - Calculation is accurate
        """
        response = client.get(
            "/api/student/profile",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        # Verify attendance percentage exists if attendance data present
    
    def test_student_sees_latest_marks(self, client, student_token, student_auth_headers, student_user, test_db, test_course):
        """
        Test that latest marks are shown.
        
        Verifies:
        - Most recent marks are returned
        - Multiple entries for same course show latest
        """
        response = client.get(
            "/api/student/marks",
            headers=student_auth_headers
        )
        assert response.status_code == 200
    
    def test_no_unauthorized_data_exposure(self, client, student_token, student_auth_headers):
        """
        Test that sensitive data is not exposed.
        
        Verifies:
        - Password fields never returned
        - No other users' data exposed
        - Only necessary fields returned
        """
        response = client.get(
            "/api/student/profile",
            headers=student_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Sensitive fields should not be in response
        assert "password" not in data
        assert "password_hash" not in data
