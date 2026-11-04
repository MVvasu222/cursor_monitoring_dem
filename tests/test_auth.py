def test_valid_login(client):
    response = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    page = client.get("/")
    assert page.status_code == 200
    assert b"Add a server to begin." in page.data
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_wrong_password_stays_on_sign_in(client):
    response = client.post("/login", data={"username": "admin", "password": "wrong-pass"})
    assert response.status_code == 200
    assert b"Sign-in failed." in response.data
    assert b"wrong-pass" not in response.data
    follow = client.get("/")
    assert follow.status_code == 302
    assert follow.headers["Location"].endswith("/login")


def test_unsigned_redirect(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_sign_out(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})
    page = client.get("/")
    token = _csrf(page.data)
    response = client.post("/logout", data={"csrf_token": token})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    again = client.get("/")
    assert again.status_code == 302
    assert again.headers["Location"].endswith("/login")


def _csrf(html):
    marker = b'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    end = html.index(b'"', start)
    return html[start:end].decode()
