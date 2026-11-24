from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'notifications'

    def ready(self):
        from claims.events import ClaimApproved
        from claims.publishers import claim_approved

        from .consumers import ApprovalNotificationConsumer

        claim_approved.connect(
            ApprovalNotificationConsumer.handle,
            sender=ClaimApproved,
            dispatch_uid="notifications.approval_notification_consumer",
            weak=False,
        )
