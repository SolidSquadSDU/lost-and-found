# Claim approval event

The project publishes one business event, `ClaimApproved`, and implements one
consumer, `HandoverTaskConsumer`. Teammates can subscribe their own consumers to
the same publisher. No message broker is required.

## Event and publisher

`src/claims/events.py` defines an immutable Python dataclass:

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | `UUID` | Unique identity of this event; preserve it on redelivery. |
| `occurred_at` | `datetime` | Timezone-aware approval time. |
| `claim_id` | `int` | Approved claim. |
| `item_id` | `int` | Item being claimed. |
| `claimant_id` | `int` | User collecting the item. |
| `reporter_id` | `int` | User who reported the found item. |

`approve_claim()` in `src/claims/services.py` saves the claim as `APPROVED`,
marks its item `CLAIMED`, and preserves the existing approval notification.
These writes run in one database transaction. An `on_commit()` callback calls
`publish_claim_approved(event)` only after that transaction commits. A rollback
discards the callback.

`src/claims/publishers.py` exports the shared `claim_approved` Django signal and
`publish_claim_approved(event)`. The publisher dispatches the event synchronously
with `send_robust()`, using `ClaimApproved` as its sender. It returns the receiver
responses; Django logs receiver exceptions and continues to other receivers.

## Handover task consumer

`HandoverTaskConsumer.handle()` in `src/claims/consumers.py` creates a persisted
`HandoverTask` for arranging collection. The task links to the claim, through
which the item, claimant, and reporter are available. It stores the original
event ID, approval time, creation time, and a status initially set to `PENDING`.
The other supported status is `COMPLETED`.

`ClaimsConfig.ready()` registers the handler with a stable `dispatch_uid` and
`weak=False`, so repeated app initialization does not register it twice.

Duplicate protection is part of the database schema: `source_event_id` is unique
and `claim` is a one-to-one relationship. The consumer uses
`get_or_create(claim_id=event.claim_id, defaults=...)`. Redelivery returns the
existing task rather than creating another one or resetting its status. This
single-row effect does not require a separate processed-events table.

## Add a teammate's consumer

Implement the reaction in your own app and register it in that app's
`AppConfig.ready()`. The following is a registration example and an unfinished
receiver outline; it does not implement another consumer:

```python
# your_app/consumers.py
from claims.events import ClaimApproved


def handle_claim_approved(*, event: ClaimApproved, **kwargs):
    # Implement your own persisted reaction and duplicate protection here.
    ...
```

```python
# your_app/apps.py
from django.apps import AppConfig


class YourAppConfig(AppConfig):
    name = "your_app"

    def ready(self):
        from claims.events import ClaimApproved
        from claims.publishers import claim_approved
        from .consumers import handle_claim_approved

        claim_approved.connect(
            handle_claim_approved,
            sender=ClaimApproved,
            dispatch_uid="your_app.claim_approved",
            weak=False,
        )
```

Add your app config to `INSTALLED_APPS` and choose a `dispatch_uid` unique to
your consumer. All consumers receive the same event; each must protect its own
effect against duplicate delivery. A unique event-ID column on the effect row
can be enough. For counters or several writes, save the effect and a processed
event marker in one transaction, with a unique `(consumer_name, event_id)` key.
A shared marker keyed only by `event_id` would prevent the other consumers from
processing the event.

The teammate implementing approval notifications should move the existing
`CLAIM_APPROVED` outbox write from `approve_claim()` into their consumer and
preserve its duplicate protection. That direct write is currently retained to
keep the existing notification behavior working.

## Run and verify

From the repository root in PowerShell, using the project's virtual environment:

```powershell
.\.venv\Scripts\python.exe src/manage.py migrate
.\.venv\Scripts\python.exe src/manage.py check
.\.venv\Scripts\python.exe src/manage.py test claims.test_events -v 2
.\.venv\Scripts\python.exe src/manage.py test -v 2
```

The event tests cover successful approval, publication and task creation, plus
delivery of the same event twice producing one task. Teammates should add their
own success and duplicate-delivery tests. Django `TestCase` wraps tests in a
transaction, so use `captureOnCommitCallbacks(execute=True)` when testing the
approval publisher.

## Delivery limits

This is a synchronous, in-process mechanism without durable event storage,
automatic retries, or background workers. A receiver failure happens after
approval has committed and does not undo that approval. A process crash between
commit and dispatch can lose delivery.

To retry a failed delivery manually, call `publish_claim_approved(original_event)`
with the same event ID and original payload. Successful consumers must treat
that redelivery as a duplicate. Creating a new event ID or re-running approval
is not a substitute for retrying the original event.
