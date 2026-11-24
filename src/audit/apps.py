from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "audit"

    def ready(self):
        from claims.events import ClaimApproved
        from claims.publishers import claim_approved

        from .consumers import ApprovalAuditConsumer

        claim_approved.connect(
            ApprovalAuditConsumer.handle,
            sender=ClaimApproved,
            dispatch_uid="audit.approval_audit_consumer",
            weak=False,
        )
