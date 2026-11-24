import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("claims", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HandoverTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("source_event_id", models.UUIDField(editable=False, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("PENDING", "Pending"), ("COMPLETED", "Completed")],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("approved_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "claim",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="handover_task",
                        to="claims.claim",
                    ),
                ),
            ],
        ),
    ]
