// Lookups shared by the Classrooms and Issues pages: users, rooms and AST items by id.
import { api, isAdmin } from "./app.js";

/** Active staff by id (GET /users/directory, open to every role). An Admin also gets inactive accounts. */
export async function loadUsers(user) {
  const users = new Map();
  try {
    for (const u of await api.get("/users/directory")) users.set(u.id, u);
    if (isAdmin(user)) for (const u of await api.get("/users")) users.set(u.id, u);
  } catch { /* names fall back to "Staff #id" */ }
  return users;
}

/** A person's name, or a neutral label when the id is not known to this role. */
export function userName(users, id) {
  if (id === null || id === undefined) return "—";
  return users.get(id)?.full_name ?? `Staff #${id}`;
}

export const roomName = (room) => `${room.building}-${room.room}`;

/** Equipment/consumable items by id, with their category name. */
export async function loadItems() {
  const [items, categories] = await Promise.all([api.get("/ast/items"), api.get("/ast/categories")]);
  const names = new Map(categories.map((c) => [c.id, c.name]));
  return new Map(items.map((i) => [i.id, { ...i, category: names.get(i.category_id) ?? "" }]));
}

/** "PC-0042 · Dell OptiPlex" for an installed item. */
export function itemLabel(items, itemId) {
  const item = items.get(itemId);
  return item ? `${item.asset_tag} · ${item.model}` : `Item #${itemId}`;
}

/** HH:MM from "09:00:00". */
export const hhmm = (time) => (time ?? "").slice(0, 5);

/** Wire a <dialog>: open buttons are wired by the caller; Cancel buttons and a click on the backdrop close it. */
export function wireDialog(dialog) {
  dialog.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => dialog.close()));
  dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
}

/** The button that submitted a form (falls back to the first submit button for scripted submits). */
export const submitterOf = (event) => event.submitter ?? event.target.querySelector("[type=submit]");
