"""
State pattern for claim lifecycle.

Problem: approve/reject behavior depends on the current claim status.
Participants: ClaimState, PendingState, ApprovedState, RejectedState, get_claim_state.
"""

from items.models import Item


class ClaimTransitionError(Exception):
    """Raised when a claim status transition is not allowed."""


# State pattern: shared interface for claim lifecycle stages
class ClaimState:
    def approve(self, claim):
        raise ClaimTransitionError(
            f"Cannot approve a claim in status {claim.status}."
        )

    def reject(self, claim):
        raise ClaimTransitionError(
            f"Cannot reject a claim in status {claim.status}."
        )


class PendingState(ClaimState):
    # State pattern: Pending → Approved
    def approve(self, claim):
        claim.status = claim.Status.APPROVED
        claim.save(update_fields=["status"])
        claim.item.status = Item.Status.CLAIMED
        claim.item.save(update_fields=["status"])
        return claim

    # State pattern: Pending → Rejected
    def reject(self, claim):
        claim.status = claim.Status.REJECTED
        claim.save(update_fields=["status"])
        return claim


class ApprovedState(ClaimState):
    pass


class RejectedState(ClaimState):
    pass


def get_claim_state(claim):
    # State pattern: pick behavior from current claim.status
    states = {
        claim.Status.PENDING: PendingState(),
        claim.Status.APPROVED: ApprovedState(),
        claim.Status.REJECTED: RejectedState(),
    }
    return states[claim.status]
