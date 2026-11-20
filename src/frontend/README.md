# IT-Hub: frontend design (static HTML)

Static HTML mockups of every IT-Hub screen, built from `FEATURES.md`. There's no build step and nothing to install: unzip the folder and open `index.html` in a browser. The tabs and links between pages work.

## Pages

| File | Screen |
|---|---|
| `index.html` | Home / dashboard |
| `login.html` | Sign-in, forced password change, session expired |
| `inventory.html` | Equipment, consumables, lending |
| `classrooms.html` | Rooms, seat map (click a seat), timetable, schedule import |
| `issues.html` | Issue list, detail, timeline, report form |
| `projects.html` | Projects, task board, templates |
| `orders.html` | Order summary, list, detail, receive |
| `reports.html` | Daily reports, reviews, history |
| `admin.html` | Users, audit log, my account |
| `notifications.html` | Notifications, shift summary, status badges, messages, empty state |

## Notes

- The pages show the **Admin** view. In the Student Assistant view, Admin-only buttons are hidden.
- **Styles:** each page carries its styles in its own `<style>` block in `<head>`. The shared classes are `.card`, `.btn`, `.btn-brand`, `.b-*` (status badges), `.input` and `.nav`.
- **Palette:** brand sage `#BFE3D0` / `#173F2D`, charcoal text `#2B2F36`, teal links `#1F6B7A`, SFBU gold `#8A6A2F`, cream background `#F7F5F2`.
- **Status colours:** good `#DDF2E6`, warning `#FCEBCF`, bad `#FBDDE0`, in progress `#DCEBF9`, neutral `#EEF0F3`, final/archived `#E7E0F5`.
- **Font:** Inter, loaded from Google Fonts, so you need an internet connection for it. Without one, the pages fall back to the system font.
- **Data:** all names, numbers and records are made-up sample data.
- **Wiring to the backend:** see `docs/api/README.md` and the live `/docs` page.
