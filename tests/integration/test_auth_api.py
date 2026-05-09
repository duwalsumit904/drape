CUSTOMER_PAYLOAD = {
    "email": "test@drape.com",
    "password": "Secure123!",
    "full_name": "Test User",
    "phone": "0000000000"
}



async def test_register_returns_201(client):
    resp = await client.post("/auth/register",json=CUSTOMER_PAYLOAD)
    assert resp.status_code == 201


async def test_register_returns_correct_fields(client):
    resp = await client.post("/auth/register",json=CUSTOMER_PAYLOAD)

    data= resp.json()
    assert "user_id" in data
    assert data["email"] == CUSTOMER_PAYLOAD["email"]
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_duplicate_email_returns_409(client):
    # first registration
    await client.post("/auth/register", json=CUSTOMER_PAYLOAD)

    # second registration same email
    resp = await client.post("/auth/register", json=CUSTOMER_PAYLOAD)

    assert resp.status_code == 409


async def test_register_missing_email_returns_422(client):
    resp = await client.post("/auth/register", json={
        "password": "Secure123!",
        "full_name": "Test User",
        "phone": "9800000000"
        # email missing
    })

    assert resp.status_code == 422
async def test_login_returns_tokens(client):
    await client.post("/auth/register", json=CUSTOMER_PAYLOAD)

    resp = await client.post("/auth/login", data={
        "username": CUSTOMER_PAYLOAD["email"],
        "password": CUSTOMER_PAYLOAD["password"]
    })

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(client):
    await client.post("/auth/register", json=CUSTOMER_PAYLOAD)

    resp = await client.post("/auth/login", data={
        "username": CUSTOMER_PAYLOAD["email"],
        "password": "WrongPassword!"
    })

    assert resp.status_code == 401


async def test_login_nonexistent_email_returns_401(client):
    resp = await client.post("/auth/login", data={
        "username": "ghost@drape.com",
        "password": "Whatever123!"
    })

    assert resp.status_code == 401

async def test_get_me_with_valid_token(client):
    # register
    await client.post("/auth/register", json=CUSTOMER_PAYLOAD)

    # login
    login_resp = await client.post("/auth/login", data={
        "username": CUSTOMER_PAYLOAD["email"],
        "password": CUSTOMER_PAYLOAD["password"]
    })
    token = login_resp.json()["access_token"]

    # hit protected route
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == CUSTOMER_PAYLOAD["email"]
    assert data["user_type"] == "customer"


async def test_get_me_without_token_returns_401(client):
    resp = await client.get("/auth/me")

    assert resp.status_code == 401


async def test_get_me_with_fake_token_returns_401(client):
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer this.is.fake"}
    )

    assert resp.status_code == 401