"""API follow-ups from the frontend wiring (issue #88): assignee filter and the REPORTED history entry."""

from tests.iss.test_iss import report, transition


def test_history_starts_with_the_report(client, sa_headers, admin_headers, room, equipment):
    """US-ISS-07: the timeline's first entry is the report itself, by the reporter's account."""
    issue = report(client, sa_headers, room, equipment)
    history = client.get(f"/issues/{issue['id']}/history", headers=sa_headers).json()
    assert [(h["old_status"], h["new_status"], h["comment"]) for h in history] == [(None, "OPEN", "Reported")]
    assert history[0]["user_id"] == issue["created_by"] and history[0]["timestamp"] == issue["created_at"]


def test_issues_filter_by_assignee_on_the_server(client, sa_headers, admin_headers, room, equipment):
    """US-ISS-02: assigned_to and unassigned are SQL filters, so totals and paging stay correct."""
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    first, second, third = (report(client, sa_headers, room, equipment) for _ in range(3))
    transition(client, admin_headers, first, "ASSIGNED", assignee_id=sa_id)

    mine = client.get("/issues", headers=sa_headers, params={"assigned_to": sa_id}).json()
    assert [i["id"] for i in mine["items"]] == [first["id"]] and mine["total"] == 1
    open_ones = client.get("/issues", headers=sa_headers, params={"unassigned": True}).json()
    assert {i["id"] for i in open_ones["items"]} == {second["id"], third["id"]} and open_ones["total"] == 2
    nobody = client.get("/issues", headers=sa_headers, params={"assigned_to": 999}).json()
    assert nobody["items"] == [] and nobody["total"] == 0
