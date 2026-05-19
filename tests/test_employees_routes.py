from app import models


def test_create_get_update_delete_employee(client):
	payload = {
		"first_name": "Alice",
		"last_name": "Smith",
		"email": "alice@example.com",
		"department": "Engineering",
		"job_title": "Software Engineer",
		"status": "active",
		"hire_date": "2026-05-18",
		"dob": "1990-01-01",
		"ssn": "123-45-6789",
		"compensation": 95000,
	}

	create_response = client.post("/v1/employees", json=payload)
	assert create_response.status_code == 201
	created = create_response.json()
	assert created["first_name"] == "Alice"
	assert created["email"] == "alice@example.com"
	employee_id = created["id"]

	get_response = client.get(f"/v1/employees/{employee_id}")
	assert get_response.status_code == 200
	assert get_response.json()["last_name"] == "Smith"

	update_response = client.put(
		f"/v1/employees/{employee_id}",
		json={"job_title": "Senior Software Engineer", "status": "active"},
	)
	assert update_response.status_code == 200
	updated = update_response.json()
	assert updated["job_title"] == "Senior Software Engineer"

	delete_response = client.delete(f"/v1/employees/{employee_id}")
	assert delete_response.status_code == 204

	missing_response = client.get(f"/v1/employees/{employee_id}")
	assert missing_response.status_code == 404


def test_list_employees_with_filters(client):
	client.post(
		"/v1/employees",
		json={
			"first_name": "Alice",
			"last_name": "Smith",
			"email": "alice@example.com",
			"department": "Engineering",
			"job_title": "Software Engineer",
			"status": "active",
			"hire_date": "2024-01-15",
		},
	)
	client.post(
		"/v1/employees",
		json={
			"first_name": "Bob",
			"last_name": "Johnson",
			"email": "bob@example.com",
			"department": "HR",
			"job_title": "HR Manager",
			"status": "active",
			"hire_date": "2025-03-10",
		},
	)
	client.post(
		"/v1/employees",
		json={
			"first_name": "Carol",
			"last_name": "Inactive",
			"email": "carol@example.com",
			"department": "Engineering",
			"job_title": "Analyst",
			"status": "inactive",
			"hire_date": "2023-07-01",
		},
	)

	default_response = client.get("/v1/employees")
	assert default_response.status_code == 200
	assert len(default_response.json()) == 2

	department_response = client.get("/v1/employees", params={"department": "Engineering"})
	assert department_response.status_code == 200
	assert len(department_response.json()) == 1
	assert department_response.json()[0]["email"] == "alice@example.com"

	status_response = client.get("/v1/employees", params={"status": "inactive"})
	assert status_response.status_code == 200
	assert len(status_response.json()) == 1
	assert status_response.json()[0]["email"] == "carol@example.com"

	date_range_response = client.get(
		"/v1/employees",
		params={"hired_after": "2024-01-01", "hired_before": "2024-12-31"},
	)
	assert date_range_response.status_code == 200
	assert len(date_range_response.json()) == 1
	assert date_range_response.json()[0]["email"] == "alice@example.com"
