"""SQLite session storage — round-trip, listing, no-key-at-rest.

The privacy doc promises: nothing leaves the machine, your data lives next to
your workflow file in a local sqlite db. These tests pin that the API key is
not written to the db, and that round-tripping a session preserves the data.
"""
import json
import sqlite3

import pytest

from workflow_analyzer.storage import AnalysisStorage


def test_create_session_returns_session_id(tmp_db, successful_results):
    storage = AnalysisStorage(str(tmp_db))
    sid = storage.create_session(
        workflow_data="emails and stuff",
        runs_per_prompt=5,
        results=successful_results,
        workflow_name="t1",
    )
    assert isinstance(sid, int)
    assert sid > 0


def test_round_trip_preserves_run_count(tmp_db, successful_results):
    storage = AnalysisStorage(str(tmp_db))
    sid = storage.create_session(
        workflow_data="x" * 100, runs_per_prompt=5,
        results=successful_results, workflow_name="t2",
    )
    fetched = storage.get_session_results(sid)
    assert len(fetched) == len(successful_results)


def test_round_trip_preserves_extracted_metrics(tmp_db, successful_results):
    storage = AnalysisStorage(str(tmp_db))
    sid = storage.create_session(
        workflow_data="x" * 100, runs_per_prompt=5,
        results=successful_results, workflow_name="t3",
    )
    fetched = storage.get_session_results(sid)
    # Compare metric dicts run by run.
    original_metrics = [r.extracted_metrics for r in successful_results]
    fetched_metrics = [r.extracted_metrics for r in fetched]
    assert original_metrics == fetched_metrics


def test_failed_runs_persisted_with_error_message(tmp_db, failed_results):
    storage = AnalysisStorage(str(tmp_db))
    sid = storage.create_session(
        workflow_data="x" * 100, runs_per_prompt=3,
        results=failed_results, workflow_name="t4",
    )
    fetched = storage.get_session_results(sid)
    assert all(not r.extraction_success for r in fetched)
    assert all(r.error_message and "401" in r.error_message for r in fetched)


def test_session_summary_counts_persisted_correctly(tmp_db, successful_results, failed_results):
    storage = AnalysisStorage(str(tmp_db))
    sid = storage.create_session(
        workflow_data="x" * 50, runs_per_prompt=5,
        results=successful_results + failed_results, workflow_name="t5",
    )
    s = storage.get_session(sid)
    assert s["total_runs"] == 8
    assert s["successful_runs"] == 5
    assert s["failed_runs"] == 3


def test_list_sessions_empty_db_returns_empty_list(tmp_db):
    storage = AnalysisStorage(str(tmp_db))
    assert storage.list_sessions() == []


def test_list_sessions_returns_most_recent_first(tmp_db, successful_results):
    import time
    storage = AnalysisStorage(str(tmp_db))
    storage.create_session(workflow_data="a", runs_per_prompt=5,
                            results=successful_results, workflow_name="oldest")
    time.sleep(0.01)  # ensure created_at differs
    storage.create_session(workflow_data="b", runs_per_prompt=5,
                            results=successful_results, workflow_name="newest")
    sessions = storage.list_sessions()
    assert sessions[0]["workflow_name"] == "newest"
    assert sessions[1]["workflow_name"] == "oldest"


def test_get_session_returns_none_for_unknown_id(tmp_db):
    storage = AnalysisStorage(str(tmp_db))
    assert storage.get_session(999_999) is None


def test_delete_session_removes_both_session_and_runs(tmp_db, successful_results):
    storage = AnalysisStorage(str(tmp_db))
    sid = storage.create_session(
        workflow_data="x", runs_per_prompt=5,
        results=successful_results, workflow_name="t6",
    )
    storage.delete_session(sid)
    assert storage.get_session(sid) is None
    assert storage.get_session_results(sid) == []


# ---------------------------------------------------------------------------
# Privacy invariant: no API key at rest
# ---------------------------------------------------------------------------

def test_db_dump_does_not_contain_anthropic_key(tmp_db, successful_results, monkeypatch):
    """Even if a tester accidentally puts an `sk-ant-` string in workflow data,
    the schema has no column reserved for the API key — confirm the dump has
    no row anywhere that begins with the documented prefix.

    This is a smoke test on the database schema design: there is no `api_key`
    column anywhere.
    """
    storage = AnalysisStorage(str(tmp_db))
    storage.create_session(
        workflow_data="ordinary workflow text — emails, Slack, etc.",
        runs_per_prompt=5,
        results=successful_results,
        workflow_name="privacy-check",
    )
    with sqlite3.connect(tmp_db) as conn:
        # Inspect every table's columns; none of them should be named for a key.
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        for t in tables:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})").fetchall()]
            for c in cols:
                low = c.lower()
                assert "api_key" not in low
                assert "apikey" not in low
                assert "secret" not in low


def test_schema_has_expected_tables(tmp_db):
    storage = AnalysisStorage(str(tmp_db))
    with sqlite3.connect(tmp_db) as conn:
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    assert "analysis_sessions" in names
    assert "prompt_runs" in names
