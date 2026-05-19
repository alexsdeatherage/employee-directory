from app import models


def test_import_employees_json_upserts_and_succeeds(client, db_session):
	response = client.post(
		"/v1/employees/import",
		json=[
			{
				"first_name": "Alice",
				"last_name": "Smith",
				"email": "alice@example.com",
				"department": "Engineering",
				"job_title": "Software Engineer",
			},
			{
				"first_name": "Bob",
				"last_name": "Jones",
				"email": "bob@example.com",
				"department": "HR",
				"job_title": "HR Manager",
			},
		],
	)

	assert response.status_code == 200
	summary = response.json()
	assert summary["total"] == 2
	assert summary["succeeded"] == 2
	assert summary["failed"] == 0
	assert summary["errors"] == []

	count = db_session.query(models.Employee).count()
	assert count == 2


def test_import_employees_csv_reports_row_errors_and_updates_existing(client, db_session):
	create_existing = client.post(
		"/v1/employees",
		json={
			"first_name": "Alice",
			"last_name": "Smith",
			"email": "alice@example.com",
			"department": "Engineering",
			"job_title": "Software Engineer",
		},
	)
	assert create_existing.status_code == 201
	existing_id = create_existing.json()["id"]

	csv_payload = (
		"first_name,last_name,email,department,job_title\n"
		"Alice,Smith,alice@example.com,Engineering,Staff Engineer\n"
		"Bob,,bob@example.com,HR,HR Manager\n"
	)

	response = client.post(
		"/v1/employees/import",
		data=csv_payload,
		headers={"Content-Type": "text/csv"},
	)

	assert response.status_code == 200
	summary = response.json()
	assert summary["total"] == 2
	assert summary["succeeded"] == 1
	assert summary["failed"] == 1
	assert len(summary["errors"]) == 1
	assert summary["errors"][0]["row"] == 2

	updated = client.get(f"/v1/employees/{existing_id}")
	assert updated.status_code == 200
	assert updated.json()["job_title"] == "Staff Engineer"

	assert db_session.query(models.Employee).filter(models.Employee.email == "alice@example.com").count() == 1
