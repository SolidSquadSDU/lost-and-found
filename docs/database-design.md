# Database Design — Campus Lost-and-Found System

**Team:** Solid Squad  
**Milestone:** 3 — Working Prototype and Design Evidence  
**Backend:** Django ORM (Python)  
**Current database:** SQLite  
**Planned database:** PostgreSQL

## 1. Purpose and Scope

The database supports the main prototype workflow: reporting a found item, submitting an ownership claim, and approving or rejecting that claim.

The system follows a Django Modular Monolith architecture with three implemented applications:

- `items` — stores information about found items.
- `claims` — manages ownership claims.
- `notifications` — stores notification events.

All applications share one relational database and use Django ORM.

## 2. Database Entities

| Entity | Main Fields | Responsibility |
|---|---|---|
| User (`auth_user`) | id, username, email | Stores user information using Django's built-in authentication system |
| Item (`items_item`) | id, reporter_id, title, description, found_location, status, created_at | Stores reported found items |
| Claim (`claims_claim`) | id, item_id, claimant_id, reason, status, created_at | Stores ownership claims |
| NotificationOutbox (`notifications_notificationoutbox`) | id, claim_id, event_type, status, created_at, processed_at | Stores notification events for later processing |

## 3. Relationships

The database uses four main one-to-many relationships:

1. **User → Item:** One user can report multiple found items.
2. **User → Claim:** One user can submit multiple claims for different items.
3. **Item → Claim:** One item can receive claims from multiple users.
4. **Claim → NotificationOutbox:** One claim can generate multiple notification events.

Foreign keys use `on_delete=PROTECT` to prevent deletion of referenced objects through Django ORM while related records exist.

## 4. Data Integrity and Business Rules

The following constraints are implemented:

- `UniqueConstraint(item, claimant)` prevents duplicate claims for the same item by the same user.
- `UniqueConstraint(claim, event_type)` prevents duplicate notification events of the same type for a claim.
- Foreign keys maintain relationships between the tables.
- The application service prevents users from claiming their own reported items.
- Only items with status `AVAILABLE` can receive new claims.

### Status Values

**Item:**
- `AVAILABLE`
- `CLAIMED`
- `RETURNED`

**Claim:**
- `PENDING`
- `APPROVED`
- `REJECTED`

**NotificationOutbox:**
- `PENDING`
- `SENT`
- `FAILED`

### Claim Lifecycle

The backend implements the State design pattern to manage claim transitions.

Approving a pending claim changes its status to `APPROVED` and updates the corresponding item to `CLAIMED`.

The service layer also creates notification events in the outbox.

## 5. Migrations and Implementation

The database schema is implemented using Django models and migrations.

Initial migrations:

- `items/migrations/0001_initial.py`
- `claims/migrations/0001_initial.py`
- `notifications/migrations/0001_initial.py`

### Item Status Migration

The original Item migration used the stored values `Available` and `ClAIMED`.

These values were corrected in the model to `AVAILABLE` and `CLAIMED`.

The additional migration:

`items/migrations/0002_fix_item_status_values.py`

uses `AlterField` to update the field choices and default value.

The original migration is preserved to maintain migration history.

**Important:** The second migration updates the field definition but does not automatically convert existing records. Databases containing legacy values may require a separate data migration using `RunPython`.

## 6. Automated Testing

Five automated database tests were implemented using Django's `TestCase`:

| Test | Purpose |
|---|---|
| Successful Claim Creation | Verifies that claims are stored correctly |
| Duplicate Claim Rejection | Verifies the unique constraint |
| Protected Item Deletion | Verifies foreign-key deletion protection |
| Notification Creation | Verifies notification persistence |
| Duplicate Notification Rejection | Verifies notification uniqueness |

Tests run against an isolated Django test database without external services.

Run tests from the `src` directory:

```bash
python manage.py migrate
python manage.py test claims notifications -v 2
```

## 7. ER Diagram

The Entity Relationship Diagram was created using dbdiagram.io.

The diagram illustrates database entities, primary keys, foreign keys, relationships, and unique constraints.

Files:

- [ER Diagram](database-erd.png)
- [DBML Source](database-erd.dbml)

## 8. Limitations and Future Improvements

The current implementation uses SQLite for development. PostgreSQL remains the planned database for production.

Future improvements include:

- Integrating University SSO.
- Adding database support for automated item matching.
- Implementing asynchronous notification delivery and retries.
- Testing PostgreSQL deployment and performance.
- Migrating legacy Item status values when necessary.

The current database implementation provides the persistence and data-integrity foundation for the Milestone 3 working prototype.
