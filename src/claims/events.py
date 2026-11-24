"""Business facts shared by the claim publisher and all team consumers."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ClaimApproved:
    event_id: UUID
    occurred_at: datetime
    claim_id: int
    item_id: int
    claimant_id: int
    reporter_id: int
