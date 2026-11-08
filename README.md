# Campus Lost-and-Found System

Students, teachers, staff, and security workers often lose or find personal items on campus. Information is currently spread across messaging groups, social media, and security desks. The Campus Lost-and-Found System provides one place to report, search for, match, claim, and safely return items.

Built by Solid Squad.

## Working prototype

One coherent flow is implemented: **report a found item → claim it → approve the claim**.

| Step | What happens |
| --- | --- |
| Input | `demo_claim_flow` calls the services (HTTP views are TODO fillers) |
| Logic | `items.services` + `claims.services` + State pattern transitions |
| Storage | Django models (`Item`, `Claim`, `NotificationOutbox`) in SQLite |
| Result | Printed item/claim/notification status; also visible in `/admin/` |

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "django==6.1.2"
python src/manage.py migrate
python src/manage.py demo_claim_flow
```

Example output:

```text
Demo claim flow completed
Item #1: Black backpack [CLAIMED]
Claim #1: APPROVED by claimant
Notification: CLAIM_CREATED [PENDING]
Notification: CLAIM_APPROVED [PENDING]
```

HTTP views, URL handlers, and automated tests are intentionally left as TODO fillers.

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
├── docs/                 # architecture notes and decisions
└── src/
    ├── manage.py
    ├── lostandfound/     # project settings and root URLs
    ├── items/            # report found items
    ├── claims/           # claim lifecycle + State pattern + demo command
    └── notifications/    # notification outbox rows
```

## Architecture notes

Planned apps: `accounts`, `items`, `matching`, `claims`, `notifications`.

This prototype implements the report-and-claim path with `items`, `claims`, and `notifications` only.

- [Architecture](docs/architecture.md)
- [ADR-001: Django modular monolith](docs/adr_001.md)
