async def test_db_session_works(db_session):
    assert db_session is not None

async def test_client_works(client):
    resp = await client.get("/docs")
    assert resp.status_code == 200