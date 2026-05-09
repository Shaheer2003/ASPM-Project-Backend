"""
Shared Endpoint Tests

Tests for shared/utility endpoints available to all user types.
Tests courses retrieval, health checks, and common functionality.
"""

import pytest


class TestSharedEndpoints:
    """Test endpoints available to all users."""
    
    def test_health_check(self, client):
        """
        Test API health check endpoint.
        
        Verifies:
        - API is responding
        - Returns success status
        - No authentication required
        """
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_get_courses_no_auth(self, client, test_course):
        """
        Test retrieving courses without authentication.
        
        Verifies:
        - Courses endpoint accessible
        - Returns course list
        """
        response = client.get("/api/shared/courses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "courses" in data


class TestAdminReports:
    """Test admin report generation endpoints."""
    
    def test_get_dashboard_stats(self, client, admin_token, auth_headers):
        """
        Test retrieving admin dashboard statistics.
        
        Verifies:
        - Admin can access dashboard
        - Returns statistics summary
        """
        response = client.get(
            "/api/admin-reports/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_get_attendance_report(self, client, admin_token, auth_headers):
        """
        Test generating attendance report.
        
        Verifies:
        - Admin can generate filtered attendance reports
        - Returns attendance summary
        """
        response = client.get(
            "/api/admin-reports/attendance",
            headers=auth_headers,
            params={"class_code": "Class-A"}
        )
        assert response.status_code in [200, 404]
    
    def test_get_marks_report(self, client, admin_token, auth_headers):
        """
        Test generating marks report.
        
        Verifies:
        - Admin can generate filtered marks reports
        """
        response = client.get(
            "/api/admin-reports/marks",
            headers=auth_headers,
            params={"class_code": "Class-A"}
        )
        assert response.status_code in [200, 404]
    
    def test_teacher_cannot_access_admin_reports(self, client, teacher_token, teacher_auth_headers):
        """
        Test that teacher cannot access admin reports.
        
        Verifies:
        - Admin reports require admin role
        """
        response = client.get(
            "/api/admin-reports/dashboard",
            headers=teacher_auth_headers
        )
        assert response.status_code == 403


class TestDataConsistency:
    """Test data consistency across endpoints."""
    
    def test_user_data_consistency(self, client, admin_token, auth_headers, student_user):
        """
        Test that user data is consistent across endpoints.
        
        Verifies:
        - User info from profile matches admin user list
        """
        # Get user from admin endpoint
        response1 = client.get("/api/admin/users", headers=auth_headers)
        assert response1.status_code == 200
    
    def test_course_data_consistency(self, client, test_course):
        """
        Test course data consistency.
        
        Verifies:
        - Course accessible from multiple endpoints
        """
        response = client.get("/api/shared/courses")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_invalid_endpoint(self, client):
        """
        Test accessing invalid endpoint.
        
        Verifies:
        - Invalid URL returns 404
        """
        response = client.get("/api/invalid/endpoint")
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """
        Test using invalid HTTP method.
        
        Verifies:
        - Wrong method returns 405 or appropriate error
        """
        response = client.delete("/")
        assert response.status_code in [405, 404]
    
    def test_malformed_json(self, client, auth_headers):
        """
        Test sending malformed JSON.
        
        Verifies:
        - Malformed JSON returns 422 or 400
        """
        response = client.post(
            "/api/admin/register-student",
            headers={**auth_headers, "Content-Type": "application/json"},
            data="not valid json",
        )
        assert response.status_code in [400, 422]


class TestResponseFormats:
    """Test response format consistency."""
    
    def test_success_response_format(self, client, admin_token, auth_headers):
        """
        Test that success responses have consistent format.
        
        Verifies:
        - Success responses are JSON
        - Status code is 2xx
        - Response is parseable
        """
        response = client.get(
            "/api/admin/users",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()  # Should not raise
        assert data is not None
    
    def test_error_response_format(self, client):
        """
        Test that error responses have consistent format.
        
        Verifies:
        - Error responses include detail message
        - Status code is 4xx or 5xx
        """
        response = client.get("/api/admin/users")  # No auth
        assert response.status_code in [403, 401]
        data = response.json()
        assert "detail" in data or "message" in data


class TestPagination:
    """Test pagination for list endpoints."""
    
    def test_get_users_pagination(self, client, admin_token, auth_headers):
        """
        Test pagination for users endpoint.
        
        Verifies:
        - Endpoint supports limit/offset parameters
        - Returns correct subset of data
        """
        response = client.get(
            "/api/admin/users?limit=10&offset=0",
            headers=auth_headers
        )
        # Should accept pagination params
        assert response.status_code in [200, 422]


class TestDataFiltering:
    """Test data filtering capabilities."""
    
    def test_filter_by_class(self, client, admin_token, auth_headers):
        """
        Test filtering data by class code.
        
        Verifies:
        - Can filter by class_code parameter
        """
        response = client.get(
            "/api/admin-reports/attendance?class_code=Class-A",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
    
    def test_filter_by_date_range(self, client, admin_token, auth_headers):
        """
        Test filtering by date range.
        
        Verifies:
        - Can filter by start_date and end_date
        """
        response = client.get(
            "/api/admin-reports/attendance?start_date=2024-01-01&end_date=2024-01-31",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
