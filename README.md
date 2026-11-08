# Campus Lost-and-Found System

Students, teachers, staff, and security workers often lose or find personal items on campus. Information is currently spread across messaging groups, social media, and security desks. The Campus Lost-and-Found System provides one place to report, search for, match, claim, and safely return items.

Built by Solid Squad.

## Working prototype

One coherent flow is implemented: **report a found item → claim it → approve the claim**.

| Step | What happens |
| --- | --- |
| Input | Web forms or `demo_claim_flow` |
| Logic | `items.services` + `claims.services` + State pattern transitions |
| Storage | Django models (`Item`, `Claim`, `NotificationOutbox`) in SQLite |
| Result | Pages under `/items/` and `/claims/`; also `/admin/` |

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "django==6.1.2"
python src/manage.py migrate
python src/manage.py demo_claim_flow
python src/manage.py runserver
```

Open http://127.0.0.1:8000/

Demo users (password `pass123` for both):

- `reporter` — reports items and approves/rejects claims
- `claimant` — submits claims

CLI demo still works:

```text
Demo claim flow completed
Item #1: Black backpack [CLAIMED]
Claim #1: APPROVED by claimant
Notification: CLAIM_CREATED [PENDING]
Notification: CLAIM_APPROVED [PENDING]
```

Frontend is intentionally simple. Remaining work is marked with `TODO` in templates and views (SSO login, photo upload, filters, API routes, tests).

## Design pattern: State

- **Problem:** Approve and reject behave differently depending on the claim lifecycle stage. Illegal moves (for example approving an already rejected claim) must be blocked, and approval must also mark the item as claimed.
- **Pattern used:** State (behavioral).
- **Participants:** `ClaimState`, `PendingState`, `ApprovedState`, `RejectedState`, and `get_claim_state()` in `src/claims/states.py`. Services call the current state instead of branching on status inline.
- **Why a simpler direct solution was insufficient:** Putting `if claim.status == ...` checks in services/views would scatter transition rules, duplicate side effects (item status + notification outbox), and make illegal transitions easy to miss as the lifecycle grows.

Short `# State pattern:` comments in `src/claims/states.py` and `src/claims/services.py` mark where the pattern is applied.

## Project layout

```text
lost-and-found/
├── README.md
├── docs/
└── src/
    ├── manage.py
    ├── templates/        # simple HTML UI
    ├── lostandfound/
    ├── items/
    ├── claims/
    └── notifications/
```

## Architecture notes

Planned apps: `accounts`, `items`, `matching`, `claims`, `notifications`.

This prototype implements the report-and-claim path with `items`, `claims`, and `notifications` only.

- [Architecture](docs/architecture.md)
- [ADR-001: Django modular monolith](docs/adr_001.md)
