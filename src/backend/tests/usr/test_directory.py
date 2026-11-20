"""GET /users/directory: active staff for pickers, open to every logged-in user (#83)."""


def make_user(client, admin_headers, name, email, school_id, role="STUDENT_ASSISTANT"):
    response = client.post("/users", headers=admin_headers, json={
        "full_name": name, "email": email, "school_id": school_id, "role": role,
        "temporary_password": "TempPass1234",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_a_student_assistant_can_list_active_staff_with_minimal_fields(client, admin_headers, sa_headers):
    make_user(client, admin_headers, "Ana Lopez", "ana@sfbu.edu", "SA-002")
    response = client.get("/users/directory", headers=sa_headers)
    assert response.status_code == 200
    entries = response.json()
    assert [e["full_name"] for e in entries] == ["Ana Lopez", "Sam Assistant", "System Administrator"]
    assert set(entries[0]) == {"id", "full_name", "role"}  # no email, school id or login data


def test_inactive_accounts_are_left_out(client, admin_headers, sa_headers):
    gone = make_user(client, admin_headers, "Old Helper", "old@sfbu.edu", "SA-009")
    client.patch(f"/users/{gone}", headers=admin_headers, json={"status": "INACTIVE"})
    names = [e["full_name"] for e in client.get("/users/directory", headers=sa_headers).json()]
    assert "Old Helper" not in names


def test_q_filters_by_part_of_the_name_case_insensitively(client, admin_headers, sa_headers):
    make_user(client, admin_headers, "Ana Lopez", "ana@sfbu.edu", "SA-002")
    response = client.get("/users/directory", params={"q": "lop"}, headers=sa_headers)
    assert [e["full_name"] for e in response.json()] == ["Ana Lopez"]


def test_the_directory_needs_a_login(client):
    assert client.get("/users/directory").status_code == 401


def test_the_admin_only_user_list_is_unchanged(client, sa_headers):
    assert client.get("/users", headers=sa_headers).status_code == 403
