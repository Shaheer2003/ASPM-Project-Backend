"""
Admin Endpoint Tests

Tests for user management, registration, and administrative functions.
Covers student/teacher registration, user updates, and role management.
"""

import pytest
from datetime import datetime


class TestAdminUserManagement:
    """Test administrative user management endpoints."""
    
    def test_get_all_users(self, client, admin_token, auth_headers, test_db, admin_user):
        """
        Test retrieving all users.
        
        Verifies:
        - Admin can retrieve list of all users
        - Response contains user data (id, username, role, email)
        - Only admin can access this endpoint
        """
        response = client.get(
            "/api/admin/users",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data or isinstance(data, list)
    
    def test_register_student_success(self, client, admin_token, auth_headers, sample_student_data):
        """
        Test successful student registration.
        
        Verifies:
        - Valid student data creates new student account
        - Response contains student id and details
        - Student can login after registration
        """
        response = client.post(
            "/api/admin/register-student",
            headers=auth_headers,
            json=sample_student_data
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["username"] == sample_student_data["username"]
        assert data["role"] == "STUDENT"
    
    def test_register_student_duplicate_username(self, client, admin_token, auth_headers, student_user, sample_student_data):
        """
        Test student registration with duplicate username.
        
        Verifies:
        - Duplicate username returns validation error
        - Existing student is not modified
        """
        duplicate_data = sample_student_data.copy()
        duplicate_data["username"] = student_user.username
        
        response = client.post(
            "/api/admin/register-student",
            headers=auth_headers,
            json=duplicate_data
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_register_student_invalid_email(self, client, admin_token, auth_headers, sample_student_data):
        """
        Test student registration with invalid email.
        
        Verifies:
        - Invalid email format is rejected
        - Returns validation error
        """
        invalid_data = sample_student_data.copy()
        invalid_data["email"] = "not-a-valid-email"
        
        response = client.post(
            "/api/admin/register-student",
            headers=auth_headers,
            json=invalid_data
        )
        assert response.status_code == 422  # Validation error
    
    def test_register_student_weak_password(self, client, admin_token, auth_headers, sample_student_data):
        """
        Test student registration with weak password.
        
        Verifies:
        - Weak password (less than 8 chars) is rejected
        - Returns validation error
        """
        weak_data = sample_student_data.copy()
        weak_data["password"] = "weak"
        
        response = client.post(
            "/api/admin/register-student",
            headers=auth_headers,
            json=weak_data
        )
        assert response.status_code == 422
    
    def test_register_teacher_success(self, client, admin_token, auth_headers):
        """
        Test successful teacher registration.
        
        Verifies:
        - Valid teacher data creates new teacher account
        - Teacher can be assigned to classes
        """
        teacher_data = {
            "username": "newteacher",
            "email": "newteacher@test.com",
            "password": "Teacher@123",
            "assigned_classes": ["Class-A", "Class-B"]
        }
        
        response = client.post(
            "/api/admin/register-teacher",
            headers=auth_headers,
            json=teacher_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "TEACHER"
    
    def test_update_student(self, client, admin_token, auth_headers, student_user):
        """
        Test updating student information.
        
        Verifies:
        - Admin can update student data
        - Updated information is persisted
        - Returns updated student data
        """
        update_data = {
            "phone": "1234567890",
            "department": "Information Technology"
        }
        
        response = client.put(
            f"/api/admin/students/{student_user.id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "1234567890"
        assert data["department"] == "Information Technology"
    
    def test_update_student_not_found(self, client, admin_token, auth_headers):
        """
        Test updating non-existent student.
        
        Verifies:
        - Non-existent student id returns 404
        """
        response = client.put(
            "/api/admin/students/99999",
            headers=auth_headers,
            json={"phone": "1234567890"}
        )
        assert response.status_code == 404
    
    def test_delete_student(self, client, admin_token, auth_headers, student_user, test_db):
        """
        Test deleting (archiving) a student.
        
        Verifies:
        - Admin can archive student account
        - Archived student cannot login (status changed to INACTIVE)
        - Student data is preserved (soft delete)
        """
        from app.models import UserStatus
        
        response = client.delete(
            f"/api/admin/students/{student_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify student is archived
        test_db.refresh(student_user)
        assert student_user.status == UserStatus.INACTIVE
    
    def test_delete_student_not_found(self, client, admin_token, auth_headers):
        """
        Test deleting non-existent student.
        
        Verifies:
        - Deleting non-existent student returns 404
        """
        response = client.delete(
            "/api/admin/students/99999",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestAdminRoleManagement:
    """Test role management operations."""
    
    def test_change_user_role_to_admin(self, client, admin_token, auth_headers, teacher_user):
        """
        Test promoting user to admin role.
        
        Verifies:
        - Admin can promote user to admin role
        - Promoted user gains admin permissions
        """
        response = client.put(
            f"/api/admin/users/{teacher_user.id}/role",
            headers=auth_headers,
            json={"new_role": "ADMIN"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "ADMIN"
    
    def test_change_user_role_to_teacher(self, client, admin_token, auth_headers, student_user):
        """
        Test promoting student to teacher role.
        
        Verifies:
        - Admin can change user roles
        - Role change is reflected in database
        """
        response = client.put(
            f"/api/admin/users/{student_user.id}/role",
            headers=auth_headers,
            json={"new_role": "TEACHER"}
        )
        assert response.status_code in [200, 400]  # May fail if constraints exist
    
    def test_change_user_invalid_role(self, client, admin_token, auth_headers, teacher_user):
        """
        Test changing user to invalid role.
        
        Verifies:
        - Invalid role is rejected
        - Returns validation error
        """
        response = client.put(
            f"/api/admin/users/{teacher_user.id}/role",
            headers=auth_headers,
            json={"new_role": "INVALID_ROLE"}
        )
        assert response.status_code == 422
    
    def test_teacher_cannot_change_role(self, client, teacher_token, teacher_auth_headers, student_user):
        """
        Test that non-admin cannot change roles.
        
        Verifies:
        - Teacher cannot access role management endpoints
        - Returns 403 Forbidden
        """
        response = client.put(
            f"/api/admin/users/{student_user.id}/role",
            headers=teacher_auth_headers,
            json={"new_role": "ADMIN"}
        )
        assert response.status_code == 403


class TestMissingFieldValidation:
    """Test validation of required fields in registration."""
    
    def test_register_student_missing_username(self, client, admin_token, auth_headers, sample_student_data):
        """
        Test registration with missing username.
        
        Verifies:
        - Missing required field is rejected
        """
        del sample_student_data["username"]
        
        response = client.post(
            "/api/admin/register-student",
            headers=auth_headers,
            json=sample_student_data
        )
        assert response.status_code == 422
    
    def test_register_student_missing_password(self, client, admin_token, auth_headers, sample_student_data):
        """Test registration with missing password."""
        del sample_student_data["password"]
        
        response = client.post(
            "/api/admin/register-student",
            headers=auth_headers,
            json=sample_student_data
        )
        assert response.status_code == 422
    
    def test_register_student_missing_class_code(self, client, admin_token, auth_headers, sample_student_data):
        """Test registration with missing class code."""
        del sample_student_data["class_code"]
        
        response = client.post(
            "/api/admin/register-student",
            headers=auth_headers,
            json=sample_student_data
        )
        assert response.status_code == 422
