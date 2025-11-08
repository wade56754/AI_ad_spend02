def test_docs_available(client):
    """Swagger 文档"""
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_healthz(client):
    """健康检查"""
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_readyz(client):
    """数据库连通性"""
    resp = client.get("/readyz")
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        assert isinstance(resp.json(), dict)


def test_root_not_crash(client):
    """根路径不应返回 500"""
    resp = client.get("/")
    assert resp.status_code < 500


def test_api_prefix_exists(client):
    """确认 /api/v1 前缀存在"""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any(p.startswith("/api/v1") for p in paths.keys())
