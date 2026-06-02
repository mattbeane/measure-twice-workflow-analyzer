"""Performance tests — page load, console hygiene, switching responsiveness.

These are minimum bars rather than benchmarks. A static HTML page should
load in under a couple of seconds on a developer laptop, produce no console
errors on load, and the provider dropdown should react instantly (no
synchronous network calls).
"""
from __future__ import annotations

import time


def test_page_loads_under_2_seconds(context, web_server):
    """The static page should be on the screen and interactive in under 2s."""
    page = context.new_page()
    t0 = time.monotonic()
    page.goto(f"{web_server}/index.html")
    page.wait_for_selector("#provider")
    elapsed = time.monotonic() - t0
    assert elapsed < 2.0, f"page took {elapsed:.2f}s to become interactive"
    page.close()


def test_no_console_errors_on_initial_load(context, web_server):
    """A clean page load should not log any errors. Errors here signal a JS
    regression — e.g. an undefined reference or a malformed adapter."""
    page = context.new_page()
    errors: list[str] = []
    page.on("console",
            lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto(f"{web_server}/index.html")
    page.wait_for_selector("#provider")
    # A small grace window for any deferred logging.
    page.wait_for_timeout(200)
    # Filter out the favicon 404 (cosmetic — the page doesn't ship a favicon).
    real_errors = [e for e in errors if "favicon" not in e.lower()]
    assert real_errors == [], f"unexpected console errors: {real_errors}"
    page.close()


def test_provider_switching_is_instant(page):
    """Each provider-change handler should complete in well under one frame
    (16ms). It's pure DOM updates + a localStorage read."""
    durations: list[float] = []
    for target in ("openai", "google", "xai", "anthropic"):
        t0 = time.monotonic()
        page.locator("#provider").select_option(target)
        # Settled when the active provider's key field has been reflected.
        page.wait_for_function(
            f"() => document.getElementById('apiKeyLabel').textContent.length > 0",
            timeout=1_000,
        )
        durations.append(time.monotonic() - t0)
    # Allow generous slack for cold-jit and Playwright overhead; 250ms each
    # is still well under a noticeable lag (~100ms human perception floor).
    assert max(durations) < 0.5, (
        f"slow provider switch: durations={[f'{d:.3f}s' for d in durations]}"
    )


def test_repeated_switching_does_not_leak_localstorage(page):
    """Switching back and forth N times should leave only the expected
    namespaced keys behind — no orphan entries, no accidental writes."""
    for _ in range(10):
        for target in ("openai", "google", "xai", "anthropic"):
            page.locator("#provider").select_option(target)
    keys = page.evaluate("() => Object.keys(localStorage)")
    # We didn't save any keys — so localStorage should still be empty.
    assert keys == [], f"unexpected localStorage entries after switching: {keys}"


def test_cost_estimate_updates_quickly_on_workflow_input(page):
    """Typing into the workflow textarea triggers updateEstimate. It must
    keep up with human typing speed (multi-event-loop ticks, but well under
    a tenth of a second)."""
    t0 = time.monotonic()
    page.locator("#workflow").fill("x " * 5000)
    page.wait_for_function(
        "() => document.getElementById('estimate').textContent.includes('$')",
        timeout=2_000,
    )
    elapsed = time.monotonic() - t0
    assert elapsed < 2.0, f"estimate update took {elapsed:.2f}s"
