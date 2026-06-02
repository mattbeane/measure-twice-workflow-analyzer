"""Functional tests — user-facing features in isolation.

Save / forget key per provider, localStorage migration from the legacy
single-key scheme, budget-cap input behavior, and the empty-state inputs
that should refuse the Run button gracefully.
"""
from __future__ import annotations


def test_save_key_writes_to_namespaced_storage(page):
    page.locator("#apiKey").fill("sk-ant-test-001")
    page.locator("#saveKey").click()
    stored = page.evaluate("() => localStorage.getItem('mtso_key_anthropic')")
    assert stored == "sk-ant-test-001"


def test_save_key_does_not_pollute_other_providers(page):
    """Saving an Anthropic key must not bleed into the OpenAI slot."""
    page.locator("#apiKey").fill("sk-ant-test-002")
    page.locator("#saveKey").click()
    openai_slot = page.evaluate("() => localStorage.getItem('mtso_key_openai')")
    assert openai_slot is None


def test_forget_key_removes_only_active_provider_slot(page):
    """Save keys for Anthropic and OpenAI, switch active to Anthropic, click
    Forget → only Anthropic's slot should be gone."""
    page.evaluate("""() => {
        localStorage.setItem('mtso_key_anthropic', 'sk-ant-AAAA');
        localStorage.setItem('mtso_key_openai', 'sk-BBBB');
    }""")
    page.reload()
    page.wait_for_selector("#provider")
    page.locator("#clearKey").click()
    anthropic_after = page.evaluate("() => localStorage.getItem('mtso_key_anthropic')")
    openai_after    = page.evaluate("() => localStorage.getItem('mtso_key_openai')")
    assert anthropic_after is None
    assert openai_after == "sk-BBBB"


def test_save_key_shows_user_facing_confirmation(page):
    page.locator("#apiKey").fill("sk-ant-test-003")
    page.locator("#saveKey").click()
    status = page.locator("#keyStatus").inner_text()
    assert "saved" in status.lower()


def test_forget_key_clears_input_field(page):
    page.locator("#apiKey").fill("sk-ant-XXX")
    page.locator("#saveKey").click()
    page.locator("#clearKey").click()
    assert page.locator("#apiKey").input_value() == ""


def test_save_with_empty_field_shows_friendly_status_not_save(page):
    """Empty save shouldn't create a blank entry — that would defeat 'forget'."""
    page.locator("#apiKey").fill("")
    page.locator("#saveKey").click()
    status = page.locator("#keyStatus").inner_text()
    assert "nothing" in status.lower() or "paste" in status.lower()
    assert page.evaluate("() => localStorage.getItem('mtso_key_anthropic')") is None


# ---------------------------------------------------------------------------
# Legacy migration
# ---------------------------------------------------------------------------

def test_legacy_mtso_key_is_migrated_to_anthropic_slot(context, web_server):
    """Pre-multi-provider users had `mtso_key`. On first load they should
    seamlessly see it under the Anthropic slot, and the legacy key should
    be deleted to prevent re-migration."""
    page = context.new_page()
    page.goto(f"{web_server}/index.html")
    page.wait_for_selector("#provider")
    # Set the legacy key BEFORE the migration runs — clear localStorage so
    # the next load triggers it.
    page.evaluate("() => { localStorage.setItem('mtso_key', 'legacy-AAA'); }")
    page.reload()
    page.wait_for_selector("#provider")
    assert page.evaluate("() => localStorage.getItem('mtso_key_anthropic')") == "legacy-AAA"
    assert page.evaluate("() => localStorage.getItem('mtso_key')") is None
    page.close()


def test_legacy_migration_does_not_overwrite_existing_anthropic_slot(context, web_server):
    """If both legacy and namespaced slots are set, the namespaced slot wins
    — we don't clobber a key the user explicitly saved post-upgrade."""
    page = context.new_page()
    page.goto(f"{web_server}/index.html")
    page.wait_for_selector("#provider")
    page.evaluate("""() => {
        localStorage.setItem('mtso_key', 'OLD-LEGACY');
        localStorage.setItem('mtso_key_anthropic', 'NEW-EXPLICIT');
    }""")
    page.reload()
    page.wait_for_selector("#provider")
    assert page.evaluate("() => localStorage.getItem('mtso_key_anthropic')") == "NEW-EXPLICIT"
    page.close()


def test_no_legacy_key_means_no_anthropic_slot_created(context, web_server):
    """Brand-new user — no legacy, no saved key for any provider — nothing
    should be auto-created."""
    page = context.new_page()
    page.goto(f"{web_server}/index.html")
    page.wait_for_selector("#provider")
    page.evaluate("() => localStorage.clear()")
    page.reload()
    page.wait_for_selector("#provider")
    assert page.evaluate("() => localStorage.getItem('mtso_key_anthropic')") is None
    page.close()


# ---------------------------------------------------------------------------
# Budget input
# ---------------------------------------------------------------------------

def test_budget_input_accepts_decimal(page):
    """HTML number inputs preserve the exact string the user typed, including
    trailing zeros — so "2.50" stays "2.50". What matters is the numeric
    parse, not the textual form."""
    page.locator("#budget").fill("2.50")
    assert float(page.locator("#budget").input_value()) == 2.50


def test_budget_input_default_is_safe_positive(page):
    """The default budget value should be a non-zero hard cap so a participant
    can't accidentally rack up runaway charges on first run."""
    val = page.locator("#budget").input_value()
    assert val != ""
    assert float(val) > 0


# ---------------------------------------------------------------------------
# Run-button preconditions
# ---------------------------------------------------------------------------

def test_run_with_empty_key_shows_error_message(page):
    page.locator("#workflow").fill("some workflow data " * 30)
    page.locator("#apiKey").fill("")
    page.locator("#runBtn").click()
    err = page.locator("#err")
    err.wait_for(state="visible")
    assert "key" in err.inner_text().lower()


def test_run_with_short_workflow_shows_error_message(page):
    page.locator("#apiKey").fill("sk-ant-test")
    page.locator("#workflow").fill("too short")
    page.locator("#runBtn").click()
    err = page.locator("#err")
    err.wait_for(state="visible")
    assert "workflow" in err.inner_text().lower() or "characters" in err.inner_text().lower()
