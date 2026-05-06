"""Smoke tests — the bare minimum that proves the app is wired correctly."""


async def test_login_page_renders(async_client):
    """GET /login returns 200 with the expected form fields."""
    response = await async_client.get("/login")
    assert response.status_code == 200
    body = response.text
    assert 'name="username"' in body
    assert 'name="password"' in body


async def test_health_endpoint(async_client):
    """GET /health returns 200 with the expected payload."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_root_redirects_to_login_when_unauthenticated(async_client):
    """GET / without a session redirects to /login."""
    response = await async_client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
