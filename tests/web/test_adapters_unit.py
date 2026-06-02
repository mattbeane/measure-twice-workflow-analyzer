"""Unit tests — adapter pure-functions exposed via `window.MTSO_INTERNALS`.

Each adapter is tested in isolation: buildBody, parseResponse, auth, is401,
URL resolution. No DOM, no fetch.
"""
from __future__ import annotations

import pytest


PROVIDERS = ["anthropic", "openai", "google", "xai"]


def test_all_four_providers_present(page):
    """The registry must contain all four Tier-1 providers per Matt's spec."""
    keys = page.evaluate("() => Object.keys(window.MTSO_INTERNALS.PROVIDERS)")
    for p in PROVIDERS:
        assert p in keys, f"missing provider {p!r}"


@pytest.mark.parametrize("provider", PROVIDERS)
def test_adapter_required_shape(page, provider):
    """Every adapter must expose the same surface so the rest of the app
    can be provider-agnostic."""
    shape = page.evaluate(f"""() => {{
        const a = window.MTSO_INTERNALS.PROVIDERS["{provider}"];
        return {{
            id: a.id,
            has_model: typeof a.model === "string",
            has_label: typeof a.label === "string",
            has_pricing_in: typeof a.pricing.in === "number",
            has_pricing_out: typeof a.pricing.out === "number",
            has_per_run_in: typeof a.perRunInOverhead === "number",
            has_per_run_out: typeof a.perRunOut === "number",
            has_api_url: typeof a.apiUrl === "function",
            has_auth: typeof a.auth === "function",
            has_build_body: typeof a.buildBody === "function",
            has_parse_response: typeof a.parseResponse === "function",
            has_is401: typeof a.is401 === "function",
            has_console_url: typeof a.consoleUrl === "string",
        }};
    }}""")
    assert shape["id"] == provider
    for k, v in shape.items():
        assert v, f"{provider}: {k} failed"


def test_default_models_match_matt_spec(page):
    """Locked defaults from email 778."""
    models = page.evaluate("""() => ({
        anthropic: window.MTSO_INTERNALS.PROVIDERS.anthropic.model,
        openai:    window.MTSO_INTERNALS.PROVIDERS.openai.model,
        google:    window.MTSO_INTERNALS.PROVIDERS.google.model,
        xai:       window.MTSO_INTERNALS.PROVIDERS.xai.model,
    })""")
    assert models["anthropic"] == "claude-haiku-4-5"
    assert models["openai"]    == "gpt-4o-mini"
    assert models["google"]    == "gemini-2.5-flash"
    # xAI forced reasoning per Phase 0 — non-reasoning returns truncated junk.
    assert "reasoning" in models["xai"]


def test_anthropic_is_not_experimental_others_are(page):
    """Matt's Condition 2: non-Anthropic ships as experimental."""
    e = page.evaluate("""() => ({
        anthropic: window.MTSO_INTERNALS.PROVIDERS.anthropic.experimental,
        openai:    window.MTSO_INTERNALS.PROVIDERS.openai.experimental,
        google:    window.MTSO_INTERNALS.PROVIDERS.google.experimental,
        xai:       window.MTSO_INTERNALS.PROVIDERS.xai.experimental,
    })""")
    assert e["anthropic"] is False
    assert e["openai"] is True
    assert e["google"] is True
    assert e["xai"] is True


def test_xai_disclaimer_mentions_credit_requirement(page):
    """xAI gets the extra credit-required note (Phase 0 finding: fresh teams
    can't make API calls until credits are funded)."""
    d = page.evaluate("() => window.MTSO_INTERNALS.PROVIDERS.xai.disclaimer")
    assert "credit" in d.lower() or "credits" in d.lower()


def test_anthropic_auth_header_includes_browser_access_flag(page):
    """The CORS bypass for browser-direct calls."""
    headers = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.anthropic.auth("sk-ant-test")
    """)
    assert headers["x-api-key"] == "sk-ant-test"
    assert headers["anthropic-dangerous-direct-browser-access"] == "true"
    assert "anthropic-version" in headers


def test_openai_uses_bearer_authorization(page):
    headers = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.openai.auth("sk-test")
    """)
    assert headers["Authorization"] == "Bearer sk-test"


def test_google_auth_returns_empty_object_key_in_url(page):
    """Google's API key goes in the URL query param, not a header."""
    headers = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.google.auth("AIzaTest")
    """)
    assert headers == {}


def test_google_api_url_includes_key_param(page):
    url = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.google.apiUrl({
            model: "gemini-2.5-flash", apiKey: "AIza-secret"
        })
    """)
    assert "gemini-2.5-flash" in url
    assert "AIza-secret" in url
    assert "key=" in url


def test_xai_uses_bearer_authorization(page):
    headers = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.xai.auth("xai-test")
    """)
    assert headers["Authorization"] == "Bearer xai-test"


def test_anthropic_build_body_uses_messages_shape(page):
    body = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.anthropic.buildBody({
            model: "claude-haiku-4-5",
            system: "sys",
            userText: "hi",
            temperature: 0.7,
            maxTokens: 100,
        })
    """)
    assert body["model"] == "claude-haiku-4-5"
    assert body["max_tokens"] == 100
    assert body["temperature"] == 0.7
    assert body["system"] == "sys"
    assert body["messages"] == [{"role": "user", "content": "hi"}]


def test_openai_build_body_includes_system_as_role(page):
    """Unlike Anthropic, OpenAI uses a 'system' role in the messages array."""
    body = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.openai.buildBody({
            model: "gpt-4o-mini",
            system: "sys",
            userText: "hi",
            temperature: 0.5,
            maxTokens: 200,
        })
    """)
    assert body["messages"][0] == {"role": "system", "content": "sys"}
    assert body["messages"][1] == {"role": "user", "content": "hi"}


def test_google_build_body_disables_thinking(page):
    """Critical: Matt's spec requires Gemini's reasoning preamble disabled,
    because the tool's whole demo is run-to-run variance → reliability flag."""
    body = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.google.buildBody({
            model: "gemini-2.5-flash",
            system: "sys",
            userText: "hi",
            temperature: 0.7,
            maxTokens: 100,
        })
    """)
    assert body["generationConfig"]["thinkingConfig"]["thinkingBudget"] == 0


def test_anthropic_parse_response_extracts_text_and_tokens(page):
    parsed = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.anthropic.parseResponse({
            content: [{ type: "text", text: "hello" }],
            usage: { input_tokens: 12, output_tokens: 7 },
        })
    """)
    assert parsed["text"] == "hello"
    assert parsed["inTok"] == 12
    assert parsed["outTok"] == 7


def test_openai_parse_response_handles_missing_content(page):
    """A response with no choices shouldn't crash — return empty text."""
    parsed = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.openai.parseResponse({})
    """)
    assert parsed["text"] == ""
    assert parsed["inTok"] == 0


def test_google_parse_includes_thought_tokens_in_output(page):
    """If Gemini does emit thinking tokens (despite thinkingBudget=0), they
    must count toward output cost so the banner is honest."""
    parsed = page.evaluate("""() =>
        window.MTSO_INTERNALS.PROVIDERS.google.parseResponse({
            candidates: [{ content: { parts: [{ text: "out" }] } }],
            usageMetadata: { promptTokenCount: 8, candidatesTokenCount: 5, thoughtsTokenCount: 12 },
        })
    """)
    assert parsed["outTok"] == 17  # 5 candidates + 12 thoughts


def test_google_is_401_also_handles_403(page):
    """Google's permission errors come back as 403, not 401 — adapter must
    treat them as auth failures."""
    handled_401 = page.evaluate("() => window.MTSO_INTERNALS.PROVIDERS.google.is401(401)")
    handled_403 = page.evaluate("() => window.MTSO_INTERNALS.PROVIDERS.google.is401(403)")
    assert handled_401 is True
    assert handled_403 is True


def test_pricing_per_provider_matches_published_rates(page):
    """Cost-banner accuracy hinges on these. Spot-check against published
    rates as of late-2025 / early-2026."""
    pricing = page.evaluate("""() => ({
        anthropic: window.MTSO_INTERNALS.PROVIDERS.anthropic.pricing,
        openai:    window.MTSO_INTERNALS.PROVIDERS.openai.pricing,
        google:    window.MTSO_INTERNALS.PROVIDERS.google.pricing,
        xai:       window.MTSO_INTERNALS.PROVIDERS.xai.pricing,
    })""")
    assert pricing["anthropic"] == {"in": 1.0,   "out": 5.0}
    assert pricing["openai"]    == {"in": 0.15,  "out": 0.60}
    assert pricing["google"]    == {"in": 0.30,  "out": 2.50}
    assert pricing["xai"]       == {"in": 12.50, "out": 25.00}


def test_token_overhead_basis_matches_matt_recalibration(page):
    """Matt's commit 6e3e247 set perRunIn=1700 + perRunOut=1850 from
    4,319 real Haiku calls. Other providers inherit this as a starting point
    pending Phase 2 calibration."""
    bases = page.evaluate("""() => Object.fromEntries(
        Object.entries(window.MTSO_INTERNALS.PROVIDERS).map(
            ([k, a]) => [k, { i: a.perRunInOverhead, o: a.perRunOut }]
        )
    )""")
    assert bases["anthropic"] == {"i": 1700, "o": 1850}
    # Others inherit until Phase 2.
    for p in ("openai", "google", "xai"):
        assert bases[p]["i"] == 1700
        assert bases[p]["o"] == 1850


def test_storage_id_helper_namespaces_per_provider(page):
    ids = page.evaluate("""() => ({
        anthropic: window.MTSO_INTERNALS.providerKeyStorageId("anthropic"),
        openai:    window.MTSO_INTERNALS.providerKeyStorageId("openai"),
    })""")
    assert ids["anthropic"] == "mtso_key_anthropic"
    assert ids["openai"] == "mtso_key_openai"
    assert ids["anthropic"] != ids["openai"]


def test_legacy_storage_key_is_documented(page):
    """The migration path depends on knowing exactly what the old key was."""
    legacy = page.evaluate("() => window.MTSO_INTERNALS.LEGACY_KEY_STORAGE")
    assert legacy == "mtso_key"
