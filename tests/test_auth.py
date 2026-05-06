"""Authentication flow integration tests."""


async def test_login_with_valid_credentials_sets_cookie(demo_user_in_db, unauthed_client):
    response = await unauthed_client.post(
        "/login",
        data={"username": "demo", "password": "testpass"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "session" in response.cookies


async def test_login_with_wrong_password_redirects_with_error(demo_user_in_db, unauthed_client):
    response = await unauthed_client.post(
        "/login",
        data={"username": "demo", "password": "WRONG"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=invalid"


async def test_login_with_unknown_user_redirects_with_error(unauthed_client):
    response = await unauthed_client.post(
        "/login",
        data={"username": "ghost", "password": "anything"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=invalid"


async def test_protected_route_without_session_redirects_to_login(unauthed_client):
    response = await unauthed_client.get("/overview", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


async def test_logout_clears_session(authed_client):
    # Logout
    response = await authed_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

    # Subsequent protected request redirects (cleared cookie)
    response = await authed_client.get("/overview", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
