"""The Meta data purge is deliberately scoped to one discontinued snapshot."""

from datetime import timedelta
from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import ExternalMetricsSnapshot


class DisconnectedMetaSnapshotPurgeTests(TestCase):
    def test_purge_only_meta_preserves_google_and_affiliate(self):
        now = timezone.now()
        for source in ("META", "GOOGLE_SEARCH_CONSOLE", "ALIEXPRESS"):
            ExternalMetricsSnapshot.objects.create(
                source=source,
                period_start=now - timedelta(days=30),
                period_end=now,
                checked_at=now,
                payload={"marker": source},
            )

        migration = import_module(
            "apps.catalog.migrations.0021_purge_disconnected_meta_snapshot"
        )
        migration.purge_meta_aggregate(
            apps, SimpleNamespace(connection=connection)
        )

        self.assertFalse(ExternalMetricsSnapshot.objects.filter(source="META").exists())
        for source in ("GOOGLE_SEARCH_CONSOLE", "ALIEXPRESS"):
            self.assertEqual(
                ExternalMetricsSnapshot.objects.get(source=source).payload,
                {"marker": source},
            )

        # Idempotent: safe to re-check without deleting unrelated data.
        migration.purge_meta_aggregate(
            apps, SimpleNamespace(connection=connection)
        )
        self.assertEqual(ExternalMetricsSnapshot.objects.count(), 2)
