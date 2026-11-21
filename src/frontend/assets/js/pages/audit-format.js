// Turns audit old/new values (any JSON the backend stored) into readable text (US-RPT-07/08).

const ACRONYMS = new Set(["id", "url", "qty", "csv", "it"]);
// Single-word codes are only relabelled under these keys, so "USB" in a name stays "USB".
const CODE_KEYS = /(status|role|condition|priority|method|action|category|severity|kind|type|state)$/i;

/** "school_id" → "School ID", "due_date" → "Due date". */
export function fieldLabel(key) {
  const words = String(key).split(/[_\s]+/).filter(Boolean)
    .map((word) => ACRONYMS.has(word.toLowerCase()) ? word.toUpperCase() : word.toLowerCase());
  if (!words.length) return "";
  return words[0].charAt(0).toUpperCase() + words[0].slice(1) + (words.length > 1 ? ` ${words.slice(1).join(" ")}` : "");
}

/** One value as plain text: "—" for empty, Yes/No, "Partially arrived" for codes, lists joined. */
export function valueText(value, key = "") {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.length ? value.map((item) => valueText(item, key)).join(", ") : "—";
  if (typeof value === "object") return fieldPairs(value).map(([key, text]) => `${key}: ${text}`).join("; ") || "—";
  const text = String(value);
  const isCode = /^[A-Z][A-Z0-9]*(_[A-Z0-9]+)+$/.test(text) || (CODE_KEYS.test(key) && /^[A-Z]+$/.test(text));
  return isCode ? fieldLabel(text) : text;
}

/** [["Email", "admin@sfbu.edu"], ...] for an object; one ["Value", text] pair for anything else; [] when empty. */
export function fieldPairs(value) {
  if (value === null || value === undefined || value === "") return [];
  if (typeof value !== "object" || Array.isArray(value)) return [["Value", valueText(value)]];
  return Object.entries(value).map(([key, item]) => [fieldLabel(key), valueText(item, key)]);
}

/** The whole value on one line, for a tooltip or a narrow cell. */
export function summary(value) {
  const pairs = fieldPairs(value);
  if (!pairs.length) return "—";
  if (pairs.length === 1 && pairs[0][0] === "Value") return pairs[0][1];
  return pairs.map(([key, text]) => `${key}: ${text}`).join(" · ");
}

/** Rows for a before/after table: every field in either value, marking the ones that changed. */
export function changeRows(oldValue, newValue) {
  const before = Object.fromEntries(fieldPairs(oldValue));
  const after = Object.fromEntries(fieldPairs(newValue));
  return [...new Set([...Object.keys(before), ...Object.keys(after)])].map((field) => ({
    field, before: before[field] ?? "—", after: after[field] ?? "—", changed: (before[field] ?? "—") !== (after[field] ?? "—"),
  }));
}
