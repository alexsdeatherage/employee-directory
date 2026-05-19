def test_search_ranks_exact_before_partial(client):
    # exact match on email should rank first
    client.post(
        "/v1/employees",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "department": "Engineering",
            "job_title": "Engineer",
            "status": "active",
            "hire_date": "2024-01-01",
        },
    )
    client.post(
        "/v1/employees",
        json={
            "first_name": "Johnny",
            "last_name": "Smith",
            "email": "johnny@example.com",
            "department": "Engineering",
            "job_title": "Engineer",
            "status": "active",
            "hire_date": "2024-01-02",
        },
    )

    resp = client.get("/v1/employees/search", params={"q": "john", "limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    results = data["results"]
    assert len(results) >= 2
    # first result should be the exact short name/email match
    assert results[0]["email"] == "john@example.com"


def test_search_fuzzy_matches_name_misspelling(client):
    client.post(
        "/v1/employees",
        json={
            "first_name": "John",
            "last_name": "Appleseed",
            "email": "john.appleseed@example.com",
            "department": "Product",
            "job_title": "PM",
            "status": "active",
            "hire_date": "2023-05-01",
        },
    )

    # misspelling: Jon -> should match John via fuzzy fallback or DB similarity
    resp = client.get("/v1/employees/search", params={"q": "Jon", "limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    results = data["results"]
    assert any(r["first_name"] == "John" for r in results)


def test_search_results_do_not_expose_sensitive_fields(client):
    client.post(
        "/v1/employees",
        json={
            "first_name": "Sally",
            "last_name": "Sensitive",
            "email": "sally@example.com",
            "department": "HR",
            "job_title": "Manager",
            "status": "active",
            "hire_date": "2022-07-07",
            "dob": "1990-01-01",
            "ssn": "123-45-6789",
            "compensation": 120000,
        },
    )

    resp = client.get("/v1/employees/search", params={"q": "sally"})
    assert resp.status_code == 200
    data = resp.json()
    results = data["results"]
    assert len(results) >= 1
    first = results[0]
    # sensitive fields should not be present
    assert "ssn" not in first
    assert "dob" not in first
    assert "compensation" not in first
