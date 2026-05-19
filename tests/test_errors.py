def test_validation_error_shape_and_request_id(client):
    # missing required 'email'
    resp = client.post(
        "/v1/employees",
        json={"first_name": "NoEmail", "last_name": "User"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert "error" in body
    err = body["error"]
    assert err["code"] == "invalid_input"
    assert "details" in err
    assert "request_id" in err
    # header present
    assert "X-Request-ID" in resp.headers


def test_404_error_shape_and_request_id(client):
    resp = client.get("/v1/employees/9999")
    assert resp.status_code in (404,)
    body = resp.json()
    assert "error" in body
    err = body["error"]
    assert err["code"] == "http_error"
    assert "request_id" in err
    assert "X-Request-ID" in resp.headers
