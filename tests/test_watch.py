from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harmony360_orchestration.changes import normalize
from harmony360_orchestration.cli import main
from harmony360_orchestration.sources import Snapshot, SourceUnavailable
from harmony360_orchestration.watch import BaselineRequired, WatchStore


def release(number=1, body="### Bug Fixes\n- Fix security boundary containment", **overrides):
    return {"id": number, "tag_name": "test-1", "name": "Synthetic fixture",
            "html_url": "https://github.com/crewAIInc/crewAI/releases/tag/test-1",
            "body": body, "draft": False, "prerelease": False,
            "published_at": "2026-11-21T00:00:00Z", "updated_at": "2026-11-21T00:00:00Z", **overrides}


def advisory(**overrides):
    return {"ghsa_id": "GHSA-test-fixture", "html_url": "https://github.com/crewAIInc/crewAI/security/advisories/GHSA-test-fixture",
            "summary": "Synthetic security fixture", "severity": "high", "description": "Fixture",
            "vulnerabilities": [{"package": {"name": "crewai"}, "vulnerable_version_range": "<1.0", "patched_versions": "1.0"}],
            "published_at": "2026-11-21T00:00:00Z", "updated_at": "2026-11-21T00:00:00Z", **overrides}


def snapshot(releases=(), advisories=()):
    return Snapshot(tuple(releases), tuple(advisories), "2026-11-21T00:00:00Z")


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "watch.sqlite3"
        self.store = WatchStore(self.path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def baseline(self, source=None):
        self.store.stage(source or snapshot(), baseline=True)

    def test_initialization_is_explicit_and_cannot_reset(self):
        with self.assertRaises(BaselineRequired):
            self.store.stage(snapshot())
        self.baseline()
        with self.assertRaises(BaselineRequired):
            self.store.stage(snapshot(), baseline=True)

    def test_new_release_then_unchanged_is_quiet(self):
        self.baseline()
        alerts = self.store.stage(snapshot([release()]))
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["potential_harmony360_impact"]["classification"], "ENGINEERING_INFERENCE")
        self.store.acknowledge([a["alert_id"] for a in alerts])
        self.assertEqual(self.store.stage(snapshot([release()])), [])

    def test_pending_alert_survives_restart_and_no_new_changes(self):
        self.baseline()
        expected = self.store.stage(snapshot([release()]))
        self.store.close()
        self.store = WatchStore(self.path)
        self.assertEqual(self.store.stage(snapshot([release()])), expected)

    def test_failed_delivery_does_not_acknowledge(self):
        self.baseline()
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("harmony360_orchestration.cli.OfficialGitHubClient.fetch", return_value=snapshot([release()])), \
             patch("harmony360_orchestration.cli.atomic_write", side_effect=OSError("disk full")), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["crewai-watch", "--state", str(self.path), "--output", str(Path(self.tmp.name)/"alert.json")]), 2)
        self.assertEqual(len(self.store.pending()), 1)
        self.assertEqual(stdout.getvalue(), "")

    def test_failed_fetch_does_not_advance_state(self):
        self.baseline()
        count = self.store.db.execute("SELECT COUNT(*) FROM checks").fetchone()[0]
        with patch("harmony360_orchestration.cli.OfficialGitHubClient.fetch", side_effect=SourceUnavailable("HTTP 403")), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["crewai-watch", "--state", str(self.path)]), 2)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM checks").fetchone()[0], count)

    def test_documentation_and_cosmetic_releases_are_suppressed(self):
        self.baseline()
        docs = release(body="### Documentation\n- Update Python migration guide\n### Contributors\n- Test User")
        cosmetic = release(2, "### Bug Fixes\n- Fix spelling in a label")
        self.assertEqual(self.store.stage(snapshot([docs, cosmetic])), [])

    def test_prerelease_promotion_to_stable_alerts(self):
        self.baseline()
        self.assertEqual(self.store.stage(snapshot([release(prerelease=True)])), [])
        self.assertEqual(len(self.store.stage(snapshot([release(prerelease=False)]))), 1)

    def test_advisory_content_update_alerts_but_metadata_noise_does_not(self):
        self.baseline(snapshot(advisories=[advisory()]))
        unchanged = advisory(updated_at="2026-11-22T00:00:00Z")
        self.assertEqual(self.store.stage(snapshot(advisories=[unchanged])), [])
        changed = advisory(description="Materially revised remediation")
        alerts = self.store.stage(snapshot(advisories=[changed]))
        self.assertEqual(alerts[0]["change_status"], "UPDATED")
        self.assertEqual(alerts[0]["confirmed_upstream"]["affected_packages"][0]["patched"], "1.0")

    def test_advisory_withdrawal_is_reported(self):
        self.baseline(snapshot(advisories=[advisory()]))
        alerts = self.store.stage(snapshot(advisories=[advisory(withdrawn_at="2026-11-22T00:00:00Z")]))
        self.assertIn("withdrawn", " ".join(alerts[0]["confirmed_upstream"]["statements"]))

    def test_malformed_or_duplicate_snapshot_rejects_entire_update(self):
        self.baseline()
        for bad in (snapshot([release(), release()]), snapshot([release(html_url="https://example.org/false")])):
            with self.assertRaises(SourceUnavailable):
                self.store.stage(bad)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM seen").fetchone()[0], 0)

    def test_unchanged_cli_writes_nothing_and_removes_stale_artifact(self):
        self.baseline(snapshot([release()]))
        output = Path(self.tmp.name) / "alerts.json"
        output.write_text("stale")
        stdout = io.StringIO()
        with patch("harmony360_orchestration.cli.OfficialGitHubClient.fetch", return_value=snapshot([release()])), contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["crewai-watch", "--state", str(self.path), "--output", str(output)]), 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

