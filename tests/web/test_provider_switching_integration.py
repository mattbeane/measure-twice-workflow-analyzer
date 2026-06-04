"""Integration tests — adapter + UI binding.

Verifies that changing the provider dropdown updates the correct DOM
elements (key label, placeholder, console link, disclaimer visibility,
estimate text) in a single coordinated update.
"""
from __future__ import annotations


def test_default_load_shows_anthropic(page):
    assert page.locator("#provider").input_value() == "anthropic"
    label = page.locator("#apiKeyLabel").inner_text()
    assert "Anthropic" in label
    placeholder = page.locator("#apiKey").get_attribute("placeholder")
    assert "sk-ant" in placeholder


def test_switching_to_openai_updates_label_and_placeholder(page):
    page.locator("#provider").select_option("openai")
    assert "OpenAI" in page.locator("#apiKeyLabel").inner_text()
    assert "sk-" in page.locator("#apiKey").get_attribute("placeholder")
    # Should NOT show the anthropic prefix anymore.
    assert page.locator("#apiKey").get_attribute("placeholder") != "sk-ant-..."


def test_switching_to_google_updates_console_link(page):
    page.locator("#provider").select_option("google")
    href = page.locator("#consoleLink").get_attribute("href")
    assert "aistudio.google" in href


def test_anthropic_does_not_show_experimental_disclaimer(page):
    page.locator("#provider").select_option("anthropic")
    assert page.locator("#experimentalNotice").is_hidden()


def test_experimental_notice_stays_hidden_for_every_provider(page):
    """Experimental dropped for OpenAI/Google (Matt's call) and xAI removed,
    so the amber notice never shows for any provider now."""
    for p in ("openai", "google", "anthropic"):
        page.locator("#provider").select_option(p)
        assert page.locator("#experimentalNotice").is_hidden()


def test_provider_change_clears_key_field(page):
    """Key is per-provider — switching to a different provider with no saved
    key should show an empty input."""
    page.locator("#apiKey").fill("manual-typed-anthropic-key")
    page.locator("#provider").select_option("openai")
    assert page.locator("#apiKey").input_value() == ""


def test_provider_change_loads_saved_key_for_target(page):
    """If a key is saved for the target provider, switching loads it."""
    page.evaluate("() => localStorage.setItem('mtso_key_openai', 'sk-openai-saved')")
    page.locator("#provider").select_option("openai")
    assert page.locator("#apiKey").input_value() == "sk-openai-saved"


def test_cost_estimate_reflects_active_provider_pricing(page):
    """Switching to a provider with different pricing should change the
    displayed estimate. Per-provider banner = working integration."""
    page.locator("#workflow").fill("x " * 5000)  # ~10k chars
    page.locator("#provider").select_option("anthropic")
    anthropic_est = page.locator("#estimate").inner_text()
    page.locator("#provider").select_option("openai")
    openai_est = page.locator("#estimate").inner_text()
    # We don't assert exact values — just that they differ. Per-provider
    # banner = working integration.
    assert anthropic_est != openai_est
