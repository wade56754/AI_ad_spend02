def test_all_simple_get_endpoints(client):
    """自动检测所有无参数 GET 接口"""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    spec = res.json()
    paths = spec.get("paths", {})

    errors = []

    for route, methods in paths.items():
        get_def = methods.get("get")
        if not get_def:
            continue
        if "{" in route:  # 跳过带路径参数
            continue

        resp = client.get(route)

        # 允许 2xx~3xx、401、403、422
        if resp.status_code in (*range(200, 400), 401, 403, 422):
            continue

        # 404、500 等算错
        errors.append((route, resp.status_code))

    assert not errors, f"以下 GET 接口返回异常状态: {errors}"
