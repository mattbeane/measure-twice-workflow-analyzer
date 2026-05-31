"""User configuration: API key + defaults, stored in ~/.config/measure-twice/config.toml.

Dependency-free TOML (flat key = "value" pairs) so it works on Python 3.9+ without
tomllib. The file is human-editable. API key resolution order:
    1. explicit api_key argument
    2. ANTHROPIC_API_KEY environment variable
    3. config file
"""

import os
import re
import stat
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".config" / "measure-twice"
CONFIG_PATH = CONFIG_DIR / "config.toml"

# Defaults shipped with the tool. Overridable in the config file.
DEFAULTS = {
    "default_runs": 1000,
    "default_budget_usd": 50.0,
    "model": "claude-haiku-4-5",
}

_LINE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*=\s*(.+?)\s*$')


def _coerce(raw: str):
    """Turn a TOML-ish scalar into a Python value."""
    s = raw.strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]
    low = s.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _format(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return f'"{value}"'


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Read the config file, merged over DEFAULTS. Missing file → just DEFAULTS."""
    cfg = dict(DEFAULTS)
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = _LINE.match(line)
            if m:
                cfg[m.group(1)] = _coerce(m.group(2))
    return cfg


def save_config(updates: dict, path: Path = CONFIG_PATH) -> Path:
    """Merge `updates` into the existing config and write it back (mode 600)."""
    current = {}
    if path.exists():
        for line in path.read_text().splitlines():
            m = _LINE.match(line.strip())
            if m and not line.strip().startswith("#"):
                current[m.group(1)] = _coerce(m.group(2))
    current.update(updates)

    path.parent.mkdir(parents=True, exist_ok=True)
    body = ["# Measure Twice, Spend Once — configuration",
            "# Edit by hand or run `mtso configure`.", ""]
    for k, v in current.items():
        body.append(f"{k} = {_format(v)}")
    path.write_text("\n".join(body) + "\n")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600 — key lives here
    except OSError:
        pass
    return path


def resolve_api_key(explicit: Optional[str] = None, path: Path = CONFIG_PATH) -> Optional[str]:
    """Resolve the Anthropic API key: explicit > env > config file."""
    if explicit:
        return explicit
    env = os.environ.get("ANTHROPIC_API_KEY")
    if env:
        return env
    cfg = load_config(path)
    val = cfg.get("api_key")
    return val or None


def has_api_key(path: Path = CONFIG_PATH) -> bool:
    return resolve_api_key(path=path) is not None
