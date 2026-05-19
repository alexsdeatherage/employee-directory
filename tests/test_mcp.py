def test_mcp_employee_lookup_basic(client):
    # seed employees
    client.post(
        "/v1/employees",
        json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice.lookup@example.com",
            "department": "Engineering",
            "job_title": "Software Engineer",
            "status": "active",
        },
    )
    client.post(
        "/v1/employees",
        json={
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob.lookup@example.com",
            "department": "HR",
            "job_title": "HR Manager",
            "status": "active",
        },
    )

    resp = client.get("/mcp/tools/employee-lookup", params={"q": "engineer"})
    assert resp.status_code == 200
    body = resp.json()
    assert "tool" in body
    assert body["tool"]["name"] == "employee-lookup"
    assert "results" in body
    assert isinstance(body["results"], list)
    # results should not include sensitive fields
    if body["results"]:
        r = body["results"][0]
        assert "ssn" not in r
        assert "dob" not in r
        assert "compensation" not in r
