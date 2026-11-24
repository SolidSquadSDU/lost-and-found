from django.apps import AppConfig


class ClaimStatsConfig(AppConfig):
    name = "claim_stats"

    def ready(self):
        from claims.events import ClaimApproved
        from claims.publishers import claim_approved

        from .consumers import ApprovedClaimsStatisticsConsumer

        claim_approved.connect(
            ApprovedClaimsStatisticsConsumer.handle,
            sender=ClaimApproved,
            dispatch_uid="claim_stats.approved_claims_statistics_consumer",
            weak=False,
        )
