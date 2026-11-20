"""API follow-ups from the frontend wiring (issue #88): seat history, cancelled meetings, import example."""

from app.modules.cls.service import ScheduleManager
from tests.cls.test_cls import meeting


def test_equipment_history_follows_the_item_across_a_move(client, admin_headers, sa_headers, room, equipment):
    """US-CLS-02/03: install, condition and move/remove are listed oldest first, for any record of the item."""
    second = client.post("/classrooms", headers=admin_headers,
                         json={"location_id": 2, "capacity": 20, "room_type": "LECTURE"}).json()
    changed = client.post(f"/classroom-equipment/{equipment['id']}/condition", headers=sa_headers,
                          json={"condition": "FAULTY", "reason": "No display", "version": equipment["version"]}).json()
    moved = client.post(f"/classroom-equipment/{equipment['id']}/move", headers=sa_headers,
                        json={"to_classroom_id": second["id"], "version": changed["version"]})
    assert moved.status_code == 200, moved.text
    new_id = moved.json()["id"]

    history = client.get(f"/classroom-equipment/{new_id}/history", headers=sa_headers)
    assert history.status_code == 200
    rows = history.json()
    assert [r["action"] for r in rows] == ["INSTALL", "CONDITION", "REMOVE", "INSTALL"]
    assert [r["classroom_id"] for r in rows] == [room["id"], room["id"], room["id"], second["id"]]
    assert (rows[1]["old_condition"], rows[1]["new_condition"], rows[1]["reason"]) == ("WORKING", "FAULTY", "No display")
    assert rows[3]["new_condition"] == "FAULTY" and rows[0]["user_id"]
    assert client.get(f"/classroom-equipment/{equipment['id']}/history", headers=admin_headers).json() == rows


def test_equipment_history_of_an_unknown_record_is_404(client, sa_headers):
    assert client.get("/classroom-equipment/999/history", headers=sa_headers).status_code == 404


def test_timetable_lists_cancelled_meetings_only_on_request(client, admin_headers, sa_headers, room):
    """US-CLS-08, BR-19: cancelling keeps the record; the timetable can show it as CANCELLED."""
    entry = client.post("/schedule/entries", headers=admin_headers, json=meeting(room["id"])).json()
    client.post(f"/schedule/entries/{entry['id']}/cancel", headers=admin_headers)
    url = f"/classrooms/{room['id']}/timetable"
    day = {"day": "2026-01-05"}  # a Monday
    assert client.get(url, headers=sa_headers, params=day).json()["days"][0]["entries"] == []
    shown = client.get(url, headers=sa_headers, params=day | {"include_cancelled": True}).json()["days"][0]
    assert [(e["id"], e["status"]) for e in shown["entries"]] == [(entry["id"], "CANCELLED")]


def test_import_request_example_matches_the_importer(client, admin_headers, room, assets):
    """US-CLS-06: the documented example is a file the importer accepts."""
    schema = client.get("/openapi.json").json()["components"]["schemas"]["CsvImportCreate"]
    example = schema["examples"][0]
    lines = example["content"].splitlines()
    assert lines[0].split(",") == ScheduleManager.HEADER
    content = example["content"].replace(",Main,101,", ",Main,201,")  # the test fixture's room
    result = client.post("/schedule/imports", headers=admin_headers,
                         json={"file_name": example["file_name"], "content": content})
    assert result.status_code == 201, result.text
    assert (result.json()["rows_accepted"], result.json()["rows_rejected"]) == (1, 0)
