def test_headcount_report_groups_by_department(client):
	client.post(
		"/employees",
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
		"/employees",
		json={
			"first_name": "Bob",
			"last_name": "Johnson",
			"email": "bob@example.com",
			"department": "Engineering",
			"job_title": "DevOps Engineer",
			"status": "active",
			"hire_date": "2024-02-20",
		},
	)
	client.post(
		"/employees",
		json={
			"first_name": "Carol",
			"last_name": "Taylor",
			"email": "carol@example.com",
			"department": "HR",
			"job_title": "HR Manager",
			"status": "active",
			"hire_date": "2024-03-10",
		},
	)

	response = client.get("/reports/headcount")
	assert response.status_code == 200
	rows = {row["department"]: row["count"] for row in response.json()}
	assert rows["Engineering"] == 2
	assert rows["HR"] == 1


def test_headcount_report_applies_filters(client):
	client.post(
		"/employees",
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
		"/employees",
		json={
			"first_name": "Bob",
			"last_name": "Johnson",
			"email": "bob@example.com",
			"department": "Engineering",
			"job_title": "DevOps Engineer",
			"status": "inactive",
			"hire_date": "2024-02-20",
		},
	)
	client.post(
		"/employees",
		json={
			"first_name": "Carol",
			"last_name": "Taylor",
			"email": "carol@example.com",
			"department": "HR",
			"job_title": "HR Manager",
			"status": "active",
			"hire_date": "2025-03-10",
		},
	)

	response = client.get(
		"/reports/headcount",
		params={"status": "active", "hired_after": "2024-01-01", "hired_before": "2024-12-31"},
	)
	assert response.status_code == 200
	rows = response.json()
	assert len(rows) == 1
	assert rows[0]["department"] == "Engineering"
	assert rows[0]["count"] == 1