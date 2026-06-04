"""Test infrastructure for the browser tool.

The browser tool is a single-file static HTML page (`web/index.html`). Tests
serve it from a local HTTP thread, drive it with Playwright Chromium, and
assert on DOM / localStorage / network behavior.

No real provider API calls are made by default; tests that need to exercise
a successful response inject a mock `fetch` into the page via
`page.add_init_script`.
"""
from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WEB_DIR = REPO_ROOT / "web"


# ---------------------------------------------------------------------------
# Local HTTP server (session-scoped)
# ---------------------------------------------------------------------------

class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass  # silence the server access log so pytest output stays clean


@pytest.fixture(scope="session")
def web_server():
    """Background HTTP server serving the `web/` directory. Yields the base URL."""
    handler = lambda *a, **kw: _SilentHandler(*a, directory=str(WEB_DIR), **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    httpd.server_close()


# ---------------------------------------------------------------------------
# Per-test browser context (clean storage every test)
# ---------------------------------------------------------------------------

@pytest.fixture
def context(browser):
    """A fresh browser context per test so localStorage / cookies / IndexedDB
    are clean. Equivalent to incognito mode for that test."""
    ctx = browser.new_context()
    yield ctx
    ctx.close()


@pytest.fixture
def page(context, web_server):
    """Page loaded with the browser tool ready. Navigates to index.html and
    waits for the provider dropdown to appear before yielding."""
    p = context.new_page()
    p.goto(f"{web_server}/index.html")
    p.wait_for_selector("#provider")
    yield p
    p.close()


# ---------------------------------------------------------------------------
# Network interception helper
# ---------------------------------------------------------------------------

@pytest.fixture
def page_with_mocked_fetch(context, web_server):
    """A page where fetch() to non-local hosts is intercepted and recorded —
    so tests can verify the right provider endpoint was called without
    spending real money. The mock returns a minimal valid response per
    provider so the run path can complete."""
    intercepted_calls: list[dict] = []

    def _make_mock_fetch():
        # JS injected before any page script runs. Replaces window.fetch with
        # a recorder that returns a minimal successful Anthropic-shaped /
        # OpenAI-shaped / etc. response per provider.
        return """
        window._mtsoIntercepted = [];
        const _realFetch = window.fetch;
        window.fetch = function(url, opts) {
            const u = typeof url === "string" ? url : url.url;
            // Allow same-origin (the static page assets) to pass through.
            if (u.startsWith(window.location.origin) || u.startsWith("data:")) {
                return _realFetch.apply(this, arguments);
            }
            const body = opts?.body || "";
            window._mtsoIntercepted.push({ url: u, headers: opts?.headers || {}, body });
            // Pick the response shape from the host:
            const fake = (() => {
                if (u.includes("anthropic.com")) {
                    return { content: [{ type: "text", text: '{"x":1}' }],
                             usage: { input_tokens: 100, output_tokens: 20 },
                             model: "claude-haiku-4-5" };
                }
                if (u.includes("openai.com")) {
                    return { choices: [{ message: { content: '{"x":1}' } }],
                             usage: { prompt_tokens: 100, completion_tokens: 20 },
                             model: "gpt-4o-mini" };
                }
                if (u.includes("googleapis.com")) {
                    return { candidates: [{ content: { parts: [{ text: '{"x":1}' }] } }],
                             usageMetadata: { promptTokenCount: 100, candidatesTokenCount: 20 } };
                }
                return { _unknown: true };
            })();
            return Promise.resolve(new Response(JSON.stringify(fake), {
                status: 200,
                headers: { "content-type": "application/json" },
            }));
        };
        """

    context.add_init_script(_make_mock_fetch())
    page = context.new_page()
    page.goto(f"{web_server}/index.html")
    page.wait_for_selector("#provider")
    yield page, intercepted_calls
    page.close()
