# IT Inventory Tracker

An object-oriented inventory tracking system for an IT department. It records hardware and software assets, tracks who has them and where they are, and logs their lifecycle from purchase to disposal.

> Course project for **[Course Code] – Object-Oriented Design**, [Semester Year], [School Name].

---

## Table of Contents
- [Overview](#overview)
- [Core Features](#core-features)
- [Design](#design)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Workflow](#workflow)
- [Team](#team)
- [License](#license)

---

## Overview
IT departments manage laptops, monitors, network gear, and software licenses spread across many users and locations. This project models that domain using object-oriented principles (encapsulation, inheritance, polymorphism, and design patterns) to produce a maintainable, extensible tracking system.

## Design
Design artifacts live in [`/docs`](docs/):
- **Use case diagram** – `docs/use-case.png`
- **Class diagram** – `docs/class-diagram.png`
- **Sequence diagrams** – `docs/sequence/`
- **Design decisions** – `docs/design-decisions.md`

Key domain classes (draft):
- `Asset` (abstract) → `HardwareAsset`, `SoftwareLicense`
- `Employee`, `Location`, `Assignment`
- `InventoryService`, `AssetRepository`, `AuditLog`

Design patterns under consideration: Factory (asset creation), Observer (license-expiry alerts), Repository (data access), Strategy (report generation).

## Tech Stack
| Layer | Choice |
|---|---|
| Language | Python 3.14 |
| Build | drawio |
| Testing | |
| Storage | |
| Diagrams | draw.io |

## Repository Structure
```
.
├── docs/               # UML diagrams, requirements, design decisions
├── src/
│   ├── main/           # Application source
│   └── test/           # Unit tests
├── .github/
│   ├── ISSUE_TEMPLATE/ # Issue templates
│   └── pull_request_template.md
├── README.md
└── LICENSE
```

## Getting Started
### Prerequisites
- drawio
- Python3
- Git

### Setup
```bash
git clone https://github.com/[org-or-user]/[repo-name].git
cd [repo-name]
# build command, e.g. ./gradlew build
```

### Run tests
```bash
# e.g. ./gradlew test
```

## Workflow
1. Every task starts as an **Issue** and is tracked on the **Project board** (Tom Nguyen).
2. Create a branch from `main`: `feature/<issue#>-short-name`, `fix/<issue#>-short-name`, or `docs/<issue#>-short-name`.
3. Commit using [Conventional Commits](https://www.conventionalcommits.org/): `feat: add asset check-out (#12)`.
4. Open a Pull Request that includes `Closes #<issue#>`.
5. At least **one teammate review** is required before merging.
6. `main` is protected — no direct pushes.

## Team
| Name | Role | GitHub |
|---|---|---|


## License
[MIT](LICENSE) — or as required by the course.