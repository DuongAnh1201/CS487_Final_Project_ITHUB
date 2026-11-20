"""PATCH: null clears optional fields; required fields ignore null; task links stay link-once (#90)."""


def make_project(client, headers, **extra):
    r = client.post("/projects", headers=headers, json={"name": "Lab refresh", "start_date": "2026-01-05", **extra})
    assert r.status_code == 201, r.text
    return r.json()


def make_task(client, headers, **extra):
    r = client.post("/tasks", headers=headers, json={"title": "Re-image PCs", **extra})
    assert r.status_code == 201, r.text
    return r.json()


def test_null_clears_a_project_due_date_but_not_its_name(client, sa_headers):
    project = make_project(client, sa_headers, due_date="2026-02-01")
    r = client.patch(f"/projects/{project['id']}", headers=sa_headers, json={"due_date": None, "name": None})
    assert r.status_code == 200, r.text
    assert r.json()["due_date"] is None
    assert r.json()["name"] == "Lab refresh"


def test_null_clears_a_task_due_date_and_omitted_fields_are_kept(client, sa_headers):
    task = make_task(client, sa_headers, due_date="2026-01-20", priority="HIGH")
    r = client.patch(f"/tasks/{task['id']}", headers=sa_headers, json={"due_date": None})
    assert r.status_code == 200, r.text
    assert r.json()["due_date"] is None
    assert r.json()["priority"] == "HIGH"


def test_a_task_link_to_a_project_cannot_be_removed(client, sa_headers):
    project = make_project(client, sa_headers)
    task = make_task(client, sa_headers, project_id=project["id"])
    r = client.patch(f"/tasks/{task['id']}", headers=sa_headers, json={"project_id": None})
    assert r.status_code == 409
    assert r.json()["detail"] == "Task already belongs to a project."


def test_null_project_on_a_standalone_task_changes_nothing(client, sa_headers):
    task = make_task(client, sa_headers)
    r = client.patch(f"/tasks/{task['id']}", headers=sa_headers, json={"project_id": None})
    assert r.status_code == 200, r.text
    assert r.json()["project_id"] is None


def test_null_removes_a_report_link_but_not_its_title(client, sa_headers):
    project = make_project(client, sa_headers)
    task = make_task(client, sa_headers, project_id=project["id"])
    report = client.post("/reports", headers=sa_headers, json={
        "title": "Lab check", "project_id": project["id"], "task_id": task["id"]}).json()
    r = client.patch(f"/reports/{report['id']}", headers=sa_headers,
                     json={"project_id": None, "task_id": None, "title": None})
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["project_id"], body["task_id"], body["title"]) == (None, None, "Lab check")
