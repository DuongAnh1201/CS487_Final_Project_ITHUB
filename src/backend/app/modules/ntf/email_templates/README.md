# IT HUB email templates

There are 8 HTML email templates, built with tables and inline styles so they render in Gmail, Outlook and Apple Mail. Placeholders use `{{variable}}`; the backend renders them with Jinja2 (`app/modules/ntf/emails.py`), escaping every value.

- **Logo:** `it-hub-logo-email.png` (1200 px wide, shown at 188×56) is served with the frontend at `src/frontend/assets/brand/`; the backend passes its public address as `{{logo_url}}`. Email clients block SVG, so it is a PNG.
- **Shift summary:** loops over `tasks` (`{% for task in tasks %}`), each with `title`, `project`, `due` and `priority`.
- **Rule:** do not email users about their own actions, matching the in-app rule.

Every template also gets `subject` (used as its `<title>`). Backend additions to the original designs: small `{% if %}` blocks for a partial delivery, an order that was already open, an empty comment or description and a shift with no tasks, and `general.html` (same style) for every other event.

| File | Email | Subject | Variables |
|---|---|---|---|
| `welcome.html` | Account created | Welcome to IT HUB | `access_end`, `admin_name`, `email`, `first_name`, `login_url`, `logo_url`, `role` |
| `password-reset.html` | Password reset | Your IT HUB password was reset | `admin_name`, `login_url`, `logo_url`, `reset_at`, `support_contact` |
| `task-assigned.html` | Task assigned | {{assigner}} assigned you: {{task_title}} | `assigner`, `due_date`, `logo_url`, `priority`, `project_name`, `task_description`, `task_title`, `task_url` |
| `issue-reported.html` | Issue reported (Admins) | {{severity}} issue in {{room}}: {{issue_no}} | `auto_effect`, `category`, `description`, `issue_no`, `issue_url`, `item`, `logo_url`, `reporter`, `reporter_type`, `room`, `severity` |
| `low-stock.html` | Low stock, order created (Admins) | Stock low: {{item_name}} · order {{order_no}} created | `item_name`, `location`, `logo_url`, `on_hand`, `order_no`, `order_qty`, `order_url`, `threshold`, `unit` |
| `order-arrived.html` | Order arrived | Order {{order_no}} has arrived | `item_name`, `logo_url`, `order_no`, `order_url`, `qty_ordered`, `qty_received`, `received_at`, `vendor` |
| `report-reviewed.html` | Report reviewed | {{reviewer}} reviewed {{report_no}}: {{outcome}} | `logo_url`, `next_step`, `outcome`, `report_no`, `report_title`, `report_url`, `review_comment`, `reviewer`, `submitted_at` |
| `shift-summary.html` | Shift summary | Your open tasks for the {{shift}} shift, {{shift_date}} | `logo_url`, `sender`, `shift`, `shift_date`, `shift_date_long`, `task_count`, `tasks_url` |
