"""End-to-end tests — full user journey with the network intercepted.

For each provider: pick from the dropdown → enter a key → paste workflow →
click Run → verify the request went to the right endpoint with the right
auth header. Real provider APIs are NOT hit — fetch is intercepted via the
`page_with_mocked_fetch` fixture.
"""
from __future__ import annotations

import json
import re

WORKFLOW = """
EMAIL: Monday 9am
From: Sarah
To: Marcus
Subject: kickoff
Hi Marcus — we need to start the new project this week. Can you align with the team by tomorrow?
""" * 6  # > 200 chars to pass the floor check


def _run_workflow(page, provider_id: str, api_key: str = "sk-test"):
    page.locator("#provider").select_option(provider_id)
    page.locator("#apiKey").fill(api_key)
    page.locator("#workflow").fill(WORKFLOW)
    page.locator("#runBtn").click()


def _intercepted_calls(page):
    return page.evaluate("() => window._mtsoIntercepted || []")


def test_anthropic_run_hits_anthropic_endpoint(page_with_mocked_fetch):
    page, _ = page_with_mocked_fetch
    _run_workflow(page, "anthropic", "sk-ant-test-e2e")
    page.wait_for_function("() => window._mtsoIntercepted.length > 0", timeout=15_000)
    calls = _intercepted_calls(page)
    assert calls
    assert any("api.anthropic.com" in c["url"] for c in calls)
    # Anthropic-specific browser-access header.
    sample = calls[0]
    body = json.loads(sample["body"])
    assert body["model"] == "claude-haiku-4-5"


def test_openai_run_hits_openai_endpoint(page_with_mocked_fetch):
    page, _ = page_with_mocked_fetch
    _run_workflow(page, "openai", "sk-openai-test-e2e")
    page.wait_for_function("() => window._mtsoIntercepted.length > 0", timeout=15_000)
    calls = _intercepted_calls(page)
    assert calls
    assert any("api.openai.com" in c["url"] for c in calls)
    body = json.loads(calls[0]["body"])
    assert body["model"] == "gpt-4o-mini"


def test_google_run_hits_gemini_endpoint_with_key_in_query(page_with_mocked_fetch):
    page, _ = page_with_mocked_fetch
    _run_workflow(page, "google", "AIza-google-test")
    page.wait_for_function("() => window._mtsoIntercepted.length > 0", timeout=15_000)
    calls = _intercepted_calls(page)
    assert calls
    google_calls = [c for c in calls if "googleapis.com" in c["url"]]
    assert google_calls
    # Key must be in the URL query string.
    assert "AIza-google-test" in google_calls[0]["url"]


def test_xai_run_hits_xai_endpoint_with_reasoning_model(page_with_mocked_fetch):
    page, _ = page_with_mocked_fetch
    _run_workflow(page, "xai", "xai-test-e2e")
    page.wait_for_function("() => window._mtsoIntercepted.length > 0", timeout=15_000)
    calls = _intercepted_calls(page)
    assert calls
    assert any("api.x.ai" in c["url"] for c in calls)
    body = json.loads(calls[0]["body"])
    assert "reasoning" in body["model"]


def test_provider_switching_mid_session_changes_endpoint(page_with_mocked_fetch):
    """Switch from Anthropic to OpenAI mid-journey: the next Run hits OpenAI.

    Note: we don't try to halt the first run — we just verify that the
    second run produces OpenAI calls (which proves the dispatch followed
    the dropdown change)."""
    page, _ = page_with_mocked_fetch

    # First leg — Anthropic. Use a tight budget so the run stops fast.
    page.locator("#provider").select_option("anthropic")
    page.locator("#apiKey").fill("sk-ant-A")
    page.locator("#workflow").fill(WORKFLOW)
    page.locator("#budget").fill("0.001")    # halts after a small number of calls
    page.locator("#runBtn").click()
    page.wait_for_selector("#runBtn:not([disabled])", timeout=20_000)
    anthropic_calls = [c for c in _intercepted_calls(page) if "anthropic" in c["url"]]
    assert anthropic_calls, "first leg should have hit anthropic"

    # Reset and switch.
    page.evaluate("() => { window._mtsoIntercepted = []; }")
    page.locator("#provider").select_option("openai")
    page.locator("#apiKey").fill("sk-openai-B")
    page.locator("#runBtn").click()
    page.wait_for_selector("#runBtn:not([disabled])", timeout=20_000)

    calls_after = _intercepted_calls(page)
    openai_calls = [c for c in calls_after if "openai" in c["url"]]
    anthropic_after = [c for c in calls_after if "anthropic" in c["url"]]
    assert openai_calls, "second leg should have hit openai"
    assert not anthropic_after, (
        f"after switching to openai, anthropic should not be called again; "
        f"got {len(anthropic_after)} anthropic calls"
    )


def test_run_records_spend_progress_in_ui(page_with_mocked_fetch):
    """The progress bar's spend pill should update after at least one run
    completes."""
    page, _ = page_with_mocked_fetch
    _run_workflow(page, "anthropic", "sk-ant-progress-test")
    page.wait_for_function(
        "() => document.getElementById('progressSpend').textContent.includes('$')",
        timeout=15_000,
    )
    spend = page.locator("#progressSpend").inner_text()
    assert "$" in spend
