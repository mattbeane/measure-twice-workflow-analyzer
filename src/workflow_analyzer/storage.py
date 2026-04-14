"""SQLite storage for analysis results."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schemas import PromptRunResult


class AnalysisStorage:
    """SQLite-based storage for analysis runs."""

    def __init__(self, db_path: str = "workflow_analysis.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS analysis_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    workflow_name TEXT,
                    workflow_data TEXT NOT NULL,
                    runs_per_prompt INTEGER NOT NULL,
                    total_runs INTEGER NOT NULL,
                    successful_runs INTEGER NOT NULL,
                    failed_runs INTEGER NOT NULL,
                    total_input_tokens INTEGER NOT NULL,
                    total_output_tokens INTEGER NOT NULL,
                    total_latency_ms INTEGER NOT NULL,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS prompt_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_title TEXT NOT NULL,
                    run_number INTEGER NOT NULL,
                    raw_response TEXT NOT NULL,
                    extracted_metrics TEXT,  -- JSON
                    extraction_success INTEGER NOT NULL,
                    error_message TEXT,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
                );

                CREATE INDEX IF NOT EXISTS idx_prompt_runs_session
                ON prompt_runs(session_id);

                CREATE INDEX IF NOT EXISTS idx_prompt_runs_prompt
                ON prompt_runs(session_id, prompt_id);
            """)

    def create_session(
        self,
        workflow_data: str,
        runs_per_prompt: int,
        results: list[PromptRunResult],
        workflow_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Store a complete analysis session.

        Returns:
            Session ID
        """
        now = datetime.utcnow().isoformat()

        total_runs = len(results)
        successful_runs = sum(1 for r in results if r.extraction_success)
        failed_runs = total_runs - successful_runs
        total_input_tokens = sum(r.input_tokens for r in results)
        total_output_tokens = sum(r.output_tokens for r in results)
        total_latency_ms = sum(r.latency_ms for r in results)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO analysis_sessions (
                    created_at, workflow_name, workflow_data, runs_per_prompt,
                    total_runs, successful_runs, failed_runs,
                    total_input_tokens, total_output_tokens, total_latency_ms, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now, workflow_name, workflow_data, runs_per_prompt,
                total_runs, successful_runs, failed_runs,
                total_input_tokens, total_output_tokens, total_latency_ms, notes
            ))

            session_id = cursor.lastrowid

            # Insert all prompt runs
            for result in results:
                conn.execute("""
                    INSERT INTO prompt_runs (
                        session_id, prompt_id, prompt_title, run_number,
                        raw_response, extracted_metrics, extraction_success,
                        error_message, model, input_tokens, output_tokens,
                        latency_ms, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    result.prompt_id,
                    result.prompt_title,
                    result.run_number,
                    result.raw_response,
                    json.dumps(result.extracted_metrics) if result.extracted_metrics else None,
                    1 if result.extraction_success else 0,
                    result.error_message,
                    result.model,
                    result.input_tokens,
                    result.output_tokens,
                    result.latency_ms,
                    now
                ))

            conn.commit()

        return session_id

    def get_session(self, session_id: int) -> Optional[dict]:
        """Get session metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM analysis_sessions WHERE id = ?",
                (session_id,)
            ).fetchone()

            if row:
                return dict(row)
            return None

    def get_session_results(self, session_id: int) -> list[PromptRunResult]:
        """Get all results for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM prompt_runs WHERE session_id = ? ORDER BY prompt_id, run_number",
                (session_id,)
            ).fetchall()

            results = []
            for row in rows:
                extracted_metrics = None
                if row["extracted_metrics"]:
                    extracted_metrics = json.loads(row["extracted_metrics"])

                results.append(PromptRunResult(
                    prompt_id=row["prompt_id"],
                    prompt_title=row["prompt_title"],
                    run_number=row["run_number"],
                    raw_response=row["raw_response"],
                    extracted_metrics=extracted_metrics,
                    extraction_success=bool(row["extraction_success"]),
                    error_message=row["error_message"],
                    model=row["model"],
                    input_tokens=row["input_tokens"],
                    output_tokens=row["output_tokens"],
                    latency_ms=row["latency_ms"]
                ))

            return results

    def get_prompt_results(self, session_id: int, prompt_id: str) -> list[PromptRunResult]:
        """Get results for a specific prompt in a session."""
        all_results = self.get_session_results(session_id)
        return [r for r in all_results if r.prompt_id == prompt_id]

    def list_sessions(self, limit: int = 20) -> list[dict]:
        """List recent sessions."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM analysis_sessions ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()

            return [dict(row) for row in rows]

    def delete_session(self, session_id: int):
        """Delete a session and its results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM prompt_runs WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM analysis_sessions WHERE id = ?", (session_id,))
            conn.commit()
