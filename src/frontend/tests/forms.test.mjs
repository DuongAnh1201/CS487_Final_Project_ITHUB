// Dependency-free tests for the page form boundary. Run: node --test src/frontend/tests/forms.test.mjs
import assert from "node:assert/strict";
import test from "node:test";

globalThis.window = {};
globalThis.location = { pathname: "/app/", href: "http://localhost/app/" };
globalThis.sessionStorage = { getItem: () => null };
const { payload, field, select, notes, addDays } = await import("../assets/js/pages/forms.js");
const input = (name, value, type = "text") => ({ name, value, type });

test("database lookup IDs are numbers; borrower school IDs remain strings", () => {
  const form = { elements: [input("school_id", "S001234"), input("item_id", "12", "select-one"), input("borrower_id", "7", "select-one"), input("quantity", "3", "number"), input("note", ""), {name:"is_consumable",type:"checkbox",checked:true}] };
  assert.deepEqual(payload(form), { school_id: "S001234", item_id: 12, borrower_id: 7, quantity: 3, is_consumable: true });
});

test("directory multi-select sends the selected numeric recipient IDs", () => {
  assert.deepEqual(payload({elements:[{name:"user_ids",multiple:true,selectedOptions:[{value:"1"},{value:"8"}]}]}), {user_ids:[1,8]});
});

test("form markup escapes user text and gives labels unique targets", () => {
  const malicious = '<img src=x onerror="alert(1)">';
  const first = String(field(malicious, "name", "text", malicious));
  const second = String(field("Name", "name"));
  assert(!first.includes("<img"));
  assert(first.includes("&lt;img"));
  assert.notEqual(first.match(/id="([^"]+)"/)[1], second.match(/id="([^"]+)"/)[1]);
  assert(!String(select("Person", "user_ids", [[1,malicious]])).includes("<img"));
  assert(!String(notes(malicious)).includes("<img"));
});

test("loan date arithmetic keeps calendar dates over month/year boundaries", () => {
  assert.equal(addDays("2026-12-29",7), "2027-01-05");
  assert.equal(addDays("2026-02-26",7), "2026-03-05");
});
