from bandit.server import create_app


def test_health_endpoint():
    app = create_app()
    client = app.test_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json == {"status": "ok"}
