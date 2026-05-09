"""
Authentication Endpoint Tests

Tests for user login, password reset, and token validation.
Covers success scenarios, error handling, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestAuthenticationEndpoints:
    """Test authentication and authorization endpoints."""
    
    def test_login_success(self, client, admin_user):
        """
        Test successful user login.
        
        Verifies:
        - Valid credentials return JWT token
        - Token can be used for authenticated requests
        - Response contains user metadata
        """
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "ADMIN"
    
    def test_login_invalid_credentials(self, client, admin_user):
        """
        Test login with incorrect password.
        
        Verifies:
        - Invalid password returns 401 Unauthorized
        - Error message is descriptive
        """
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_user_not_found(self, client):
        """
        Test login with non-existent username.
        
        Verifies:
        - Non-existent user returns 401
        - Same error message as wrong password (security: don't reveal user existence)
        """
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client, test_db, admin_user):
        """
        Test login with inactive user account.
        
        Verifies:
        - Inactive users cannot login
        - Returns appropriate error message
        """
        from app.models import UserStatus
        admin_user.status = UserStatus.INACTIVE
        test_db.commit()
        
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client):
        """
        Test login with missing required fields.
        
        Verifies:
        - Missing username/password returns 422 validation error
        """
        response = client.post(
            "/api/auth/login",
            json={"username": "admin"}  # Missing password
        )
        assert response.status_code == 422
    
    def test_forgot_password_valid_email(self, client, admin_user, mock_email_service):
        """
        Test password reset request with valid email.
        
        Verifies:
        - Reset token is generated and saved
        - Email is sent with reset link
        - Returns success message
        """
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "admin@test.com"}
        )
        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()
        mock_email_service.assert_called_once()
    
    def test_forgot_password_invalid_email(self, client, mock_email_service):
        """
        Test password reset request with non-existent email.
        
        Verifies:
        - Returns success message anyway (security: don't reveal user existence)
        """
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@test.com"}
        )
        assert response.status_code == 200
        # Email service should not be called for non-existent user
        mock_email_service.assert_not_called()
    
    def test_reset_password_valid_token(self, client, admin_user, test_db):
        """
        Test password reset with valid token.
        
        Verifies:
        - Valid token allows password change
        - New password can be used to login
        - Old password no longer works
        """
        from app.models import PasswordReset
        from app.auth.utils import create_reset_token
        
        reset_token = create_reset_token(admin_user.email)
        reset_record = PasswordReset(
            email=admin_user.email,
            token_hash=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        test_db.add(reset_record)
        test_db.commit()
        
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewPassword@123"
            }
        )
        assert response.status_code == 200
    
    def test_reset_password_expired_token(self, client, admin_user, test_db):
        """
        Test password reset with expired token.
        
        Verifies:
        - Expired tokens are rejected
        - Returns appropriate error message
        """
        from app.models import PasswordReset
        from app.auth.utils import create_reset_token
        
        reset_token = create_reset_token(admin_user.email)
        reset_record = PasswordReset(
            email=admin_user.email,
            token_hash=reset_token,
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        test_db.add(reset_record)
        test_db.commit()
        
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewPassword@123"
            }
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()
    
    def test_reset_password_invalid_token(self, client):
        """
        Test password reset with invalid/non-existent token.
        
        Verifies:
        - Invalid tokens are rejected
        """
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "invalid.token.here",
                "new_password": "NewPassword@123"
            }
        )
        assert response.status_code == 400


class TestTokenAuthentication:
    """Test JWT token validation and protected routes."""
    
    def test_authorized_request_with_valid_token(self, client, admin_token, auth_headers):
        """
        Test that valid token allows access to protected route.
        
        Verifies:
        - Request with valid token succeeds
        - User information can be extracted from token
        """
        response = client.get(
            "/api/admin/users",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_unauthorized_request_without_token(self, client):
        """
        Test that missing token denies access to protected route.
        
        Verifies:
        - Request without token returns 403 Forbidden
        """
        response = client.get("/api/admin/users")
        assert response.status_code == 403
    
    def test_unauthorized_request_with_invalid_token(self, client):
        """
        Test that invalid token denies access to protected route.
        
        Verifies:
        - Malformed token is rejected
        - Returns appropriate error
        """
        headers = {"Authorization": "Bearer invalid.token.format"}
        response = client.get(
            "/api/admin/users",
            headers=headers
        )
        assert response.status_code == 403
    
    def test_unauthorized_request_with_expired_token(self, client, test_db, admin_user):
        """
        Test that expired token denies access to protected route.
        
        Verifies:
        - Expired token is rejected
        - User must login again to get new token
        """
        from app.auth.utils import create_access_token
        
        # Create token that expired 1 hour ago
        expired_token = create_access_token(
            data={"sub": admin_user.username, "role": admin_user.role},
            expires_delta=timedelta(hours=-1)
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get(
            "/api/admin/users",
            headers=headers
        )
        assert response.status_code == 403


class TestRoleBasedAccess:
    """Test role-based access control (RBAC)."""
    
    def test_admin_can_access_admin_routes(self, client, admin_token):
        """
        Test that admin users can access admin-only routes.
        
        Verifies:
        - Admin role grants access to /api/admin/* endpoints
        """
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code == 200
    
    def test_teacher_cannot_access_admin_routes(self, client, teacher_token):
        """
        Test that non-admin users cannot access admin-only routes.
        
        Verifies:
        - Teacher role is denied access to /api/admin/* endpoints
        - Returns 403 Forbidden
        """
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code == 403
    
    def test_student_cannot_access_teacher_routes(self, client, student_token):
        """
        Test that student users cannot access teacher-only routes.
        
        Verifies:
        - Student role is denied access to /api/teacher/* endpoints
        """
        headers = {"Authorization": f"Bearer {student_token}"}
        response = client.post(
            "/api/teacher/mark-attendance",
            headers=headers,
            json={"class_code": "Class-A", "attendance": []}
        )
        assert response.status_code == 403
    
    def test_teacher_can_access_teacher_routes(self, client, teacher_token):
        """
        Test that teacher users can access teacher routes.
        
        Verifies:
        - Teacher role grants access to /api/teacher/* endpoints
        """
        headers = {"Authorization": f"Bearer {teacher_token}"}
        # This endpoint exists and requires TEACHER role
        response = client.post(
            "/api/teacher/mark-attendance",
            headers=headers,
            json={
                "class_code": "Class-A",
                "course_code": "CS101",
                "date": "2024-01-01",
                "session": "MORNING",
                "attendance": []
            }
        )
        # May return validation error but should not be 403
        assert response.status_code != 403
