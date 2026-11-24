from django.apps import AppConfig


class ClaimsConfig(AppConfig):
    name = 'claims'

    def ready(self):
        from .consumers import HandoverTaskConsumer
        from .publishers import claim_approved

        claim_approved.connect(
            HandoverTaskConsumer.handle,
            dispatch_uid="claims.handover_task_consumer",
            weak=False,
        )
