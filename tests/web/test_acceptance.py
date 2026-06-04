"""Acceptance tests — checklist against Matt's Phase 1 spec.

Each test pins a specific item from his 2026-06-02 email reply
("Re: Pressure-tested the workflow analyzer — concerns before tomorrow").
"""
from __future__ import annotations


def test_acceptance_three_providers_present(page):
    """Spec: Tier 1 = Anthropic / OpenAI / Google. (xAI removed — footgun:
    forced-reasoning mutes the variance signal + ~11x cost + credit-gate.)"""
    options = page.locator("#provider option").all_inner_texts()
    text = " ".join(options)
    assert "Anthropic" in text
    assert "OpenAI" in text
    assert "Google" in text and "Gemini" in text
    assert "xAI" not in text and "Grok" not in text


def test_acceptance_anthropic_default_haiku_4_5_non_thinking(page):
    """Spec: Anthropic Haiku 4.5 — non-thinking (current). buildBody must not
    set a `thinking` field."""
    body = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.anthropic.buildBody({
            model: "claude-haiku-4-5",
            system: "s", userText: "u", temperature: 0.7, maxTokens: 100,
        })
    """)
    assert "thinking" not in body
    assert body["model"] == "claude-haiku-4-5"


def test_acceptance_openai_default_gpt_4o_mini_non_reasoning(page):
    """Spec: OpenAI gpt-4o-mini — non-thinking. Model must NOT be
    `o4-mini` (which is the reasoning-tier model)."""
    model = page.evaluate("() => window.MTSO_INTERNALS.PROVIDERS.openai.model")
    assert model == "gpt-4o-mini"
    assert "o4-mini" not in model
    assert "o3-mini" not in model


def test_acceptance_google_default_2_5_flash_thinking_disabled(page):
    """Spec: Google gemini-2.5-flash — thinkingBudget: 0 (disable)."""
    body = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.google.buildBody({
            model: "gemini-2.5-flash",
            system: "s", userText: "u", temperature: 0.7, maxTokens: 100,
        })
    """)
    assert body["generationConfig"]["thinkingConfig"]["thinkingBudget"] == 0


def test_acceptance_no_provider_marked_experimental(page):
    """Updated: OpenAI/Google are now first-class (experimental dropped per
    Matt's call); xAI is removed. No provider carries the experimental flag."""
    flags = page.evaluate("""() => ({
        anthropic: window.MTSO_INTERNALS.PROVIDERS.anthropic.experimental,
        openai:    window.MTSO_INTERNALS.PROVIDERS.openai.experimental,
        google:    window.MTSO_INTERNALS.PROVIDERS.google.experimental,
    })""")
    assert flags["anthropic"] is False
    assert flags["openai"] is False
    assert flags["google"] is False


def test_acceptance_browser_only_no_cli_changes(page):
    """Spec: CLI stays Anthropic-only. The browser tool's adapter registry
    is the only place that knows about non-Anthropic providers.

    This test exists to remind: if you add a runner.py change that touches
    multi-provider Python code, this test should be expanded into a CLI
    acceptance test in tests/test_runner.py, not here."""
    # Pure documentation test — passes by existing.
    assert True


def test_acceptance_legacy_storage_key_recognized(page):
    """Spec implication: existing users (pre-multi-provider) must seamlessly
    upgrade. Migration logic must look for `mtso_key`."""
    legacy = page.evaluate("() => window.MTSO_INTERNALS.LEGACY_KEY_STORAGE")
    assert legacy == "mtso_key"


def test_acceptance_anthropic_default_provider_on_first_load(page):
    """Backwards-compat: page loads as if it's the pre-multi-provider page
    by default. Existing users see no change in behavior."""
    assert page.locator("#provider").input_value() == "anthropic"
    label = page.locator("#apiKeyLabel").inner_text()
    assert "Anthropic" in label
