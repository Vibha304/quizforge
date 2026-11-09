import pytest


def test_register_success(client):
    res = client.post(
        "/auth/register",
        json={"email": "newstudent@bit.edu", "password": "password123", "name": "Rahul Verma", "role": "student"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newstudent@bit.edu"
    assert data["user"]["name"] == "Rahul Verma"


def test_register_duplicate_fails(client):
    client.post(
        "/auth/register",
        json={"email": "duplicate@bit.edu", "password": "password123", "name": "User 1", "role": "student"},
    )
    res = client.post(
        "/auth/register",
        json={"email": "duplicate@bit.edu", "password": "password123", "name": "User 2", "role": "student"},
    )
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()


def test_login_success(client, test_user):
    res = client.post(
        "/auth/login",
        json={"email": "teststudent@quizforge.app", "password": "testpass123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_user.email


def test_login_invalid_password(client, test_user):
    res = client.post(
        "/auth/login",
        json={"email": "teststudent@quizforge.app", "password": "wrongpassword"},
    )
    assert res.status_code == 401


def test_get_me(client, auth_headers):
    res = client.get("/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "teststudent@quizforge.app"
