// Audit values read as text, never JSON (#98). Run: node --test src/frontend/tests/audit-format.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import { changeRows, fieldLabel, fieldPairs, summary, valueText } from "../assets/js/pages/audit-format.js";

test("field names become labels", () => {
  assert.equal(fieldLabel("school_id"), "School ID");
  assert.equal(fieldLabel("due_date"), "Due date");
});

test("objects become field/value pairs with readable values", () => {
  assert.deepEqual(fieldPairs({ email: "admin@sfbu.edu", role: "ADMIN", must_change_password: true, status: "PARTIALLY_ARRIVED" }),
    [["Email", "admin@sfbu.edu"], ["Role", "Admin"], ["Must change password", "Yes"], ["Status", "Partially arrived"]]);
  assert.deepEqual(fieldPairs({ method: "password" }), [["Method", "password"]]);
  assert.deepEqual(fieldPairs(null), []);
});

test("names keep their capitals; empty values show a dash", () => {
  assert.equal(valueText("USB", "name"), "USB");
  assert.equal(valueText(null), "—");
  assert.equal(valueText(["A", "B"]), "A, B");
  assert.equal(summary({ quantity: 3, note: null }), "Quantity: 3 · Note: —");
  assert.equal(summary(5), "5");
  assert(!summary({ nested: { a: 1 } }).includes("{"));
});

test("change rows cover both sides and mark what changed", () => {
  assert.deepEqual(changeRows({ status: "ORDERED", qty: 2 }, { status: "ARRIVED", qty: 2 }), [
    { field: "Status", before: "Ordered", after: "Arrived", changed: true },
    { field: "QTY", before: "2", after: "2", changed: false },
  ]);
  assert.deepEqual(changeRows(null, null), []);
});
