"""
Unit tests for User Authentication module (Signup, Login, Me, Logout).
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_auth_signup_and_login_flow():
    test_email = "teststudent@gtu.ac.in"
    test_password = "SecurePassword123!"
    test_name = "Disha Vaghela"

    # 1. Signup test
    signup_res = client.post(
        "/api/v1/auth/signup",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": test_name,
        },
    )
    assert signup_res.status_code in (201, 400)

    if signup_res.status_code == 201:
        data = signup_res.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_email
        assert data["user"]["full_name"] == test_name

    # 2. Login test
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_email,
            "password": test_password,
        },
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Check /me endpoint with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == test_email
    assert me_data["full_name"] == test_name

    # 4. Login with invalid password
    bad_login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_email,
            "password": "WrongPassword!",
        },
    )
    assert bad_login_res.status_code == 401
