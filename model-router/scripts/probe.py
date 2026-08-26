#!/usr/bin/env python3
"""
model-router: probe.py — Check if a model provider endpoint is alive.

Works with any OpenAI-compatible API, Ollama, LM Studio, llama.cpp, vLLM,
and custom endpoints. Handles auth, timeouts, and graceful failure.

Usage:
    python3 probe.py <provider> <base_url> [api_key] [model]
    python3 probe.py ollama http://localhost:11434
    python3 probe.py custom http://192.168.1.50:1234/v1 sk-xxx gpt-oss-20b

Exit codes:
    0 = endpoint reachable, model found (or no model specified)
    1 = endpoint reachable but model not found
    2 = endpoint unreachable
    3 = auth error (401/403)
"""

import json
import sys
import urllib.error
import urllib.request

USER_AGENT = "model-router/1.0"
TIMEOUT = 10

# ── Provider-specific probe logic ────────────────────────────────────────────


def _headers(api_key=None):
    """Build request headers."""
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if api_key:
        h["Authorization"] = f"Bearer {api_key}"
    return h


def _fetch_json(url, headers, timeout=TIMEOUT):
    """Fetch JSON from a URL. Returns (data, http_status, error_msg)."""
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            try:
                return json.loads(body), resp.status, None
            except json.JSONDecodeError:
                return {}, resp.status, "invalid JSON response"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return {}, e.code, f"auth_error:{e.code}"
        return {}, e.code, f"http_error:{e.code}"
    except urllib.error.URLError as e:
        return {}, 0, f"connection_failed:{str(e.reason)}"
    except TimeoutError:
        return {}, 0, "timeout"
    except OSError as e:
        return {}, 0, f"os_error:{str(e)}"


def probe_ollama(base_url, api_key=None, model=None):
    """Probe an Ollama endpoint."""
    # Normalize URL
    url = base_url.rstrip("/")
    if not url.endswith("/api"):
        url = url.rstrip("/v1") + "/api"

    # First probe /api/tags to list models
    data, status, error = _fetch_json(f"{url}/tags", _headers(api_key))
    if error:
        if "auth_error" in error:
            return {"alive": False, "status": "auth_error", "models": [],
                    "error": "Authentication failed (401/403). Check your API key."}
        if "connection_failed" in error:
            return {"alive": False, "status": "unreachable", "models": [],
                    "error": f"Ollama not reachable at {url}. Is it running?"}
        return {"alive": False, "status": "error", "models": [],
                "error": error}

    models = []
    for m in data.get("models", []):
        name = m.get("name", "unknown")
        if name != "unknown":
            models.append(name)

    # If a specific model was requested, check it's loaded
    model_found = False
    if model:
        model_found = model in models
        # Also check without tag (e.g. "llama3" matches "llama3:latest")
        if not model_found:
            model_found = any(m.startswith(model) for m in models)

    return {
        "alive": True,
        "status": "ok",
        "provider": "ollama",
        "base_url": url,
        "models": models,
        "model_count": len(models),
        "model_found": model_found if model else None,
        "model_requested": model,
    }


def probe_openai_compatible(base_url, api_key=None, model=None):
    """Probe any OpenAI-compatible endpoint (LM Studio, vLLM, llama.cpp, custom)."""
    url = base_url.rstrip("/")
    # Ensure /v1/models path
    probe_url = f"{url}/models"
    if not probe_url.endswith("/v1/models"):
        # Try adding /v1
        probe_url = f"{url}/v1/models"

    data, status, error = _fetch_json(probe_url, _headers(api_key))
    if error:
        if "auth_error" in error:
            return {"alive": False, "status": "auth_error", "models": [],
                    "error": "Authentication failed (401/403). Check your API key."}
        if "connection_failed" in error:
            return {"alive": False, "status": "unreachable", "models": [],
                    "error": f"Endpoint not reachable at {probe_url}. Is it running?"}
        return {"alive": False, "status": "error", "models": [],
                "error": error}

    models = []
    for item in data.get("data", []):
        mid = item.get("id", item.get("key", "unknown"))
        if mid != "unknown":
            models.append(mid)

    # If a specific model was requested, check it exists
    model_found = False
    if model:
        model_found = model in models
        if not model_found:
            # Try matching without provider prefix
            short = model.split("/")[-1] if "/" in model else model
            model_found = short in models or any(short in m for m in models)

    return {
        "alive": True,
        "status": "ok",
        "provider": "openai_compatible",
        "base_url": probe_url,
        "models": models,
        "model_count": len(models),
        "model_found": model_found if model else None,
        "model_requested": model,
    }


# ── Provider Router ──────────────────────────────────────────────────────────

PROVIDER_PROBERS = {
    "ollama": probe_ollama,
    "lmstudio": probe_openai_compatible,
    "llamacpp": probe_openai_compatible,
    "vllm": probe_openai_compatible,
    "openai": probe_openai_compatible,
    "openrouter": probe_openai_compatible,
    "anthropic": probe_openai_compatible,
    "custom": probe_openai_compatible,
}


def probe(provider, base_url, api_key=None, model=None):
    """
    Probe a provider endpoint.

    Args:
        provider: One of ollama, lmstudio, llamacpp, vllm, openai, openrouter,
                  anthropic, custom
        base_url: The endpoint URL (e.g. http://localhost:11434)
        api_key: Optional API key
        model: Optional model name to check

    Returns:
        dict with alive, status, models, etc.
    """
    prober = PROVIDER_PROBERS.get(provider.lower(), probe_openai_compatible)
    try:
        return prober(base_url, api_key=api_key, model=model)
    except Exception as e:
        return {
            "alive": False,
            "status": "error",
            "models": [],
            "error": f"unexpected_error:{str(e)}",
        }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 probe.py <provider> <base_url> [api_key] [model]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python3 probe.py ollama http://localhost:11434", file=sys.stderr)
        print("  python3 probe.py ollama http://localhost:11434 '' llama3", file=sys.stderr)
        print("  python3 probe.py lmstudio http://localhost:1234/v1 sk-xxx model-name", file=sys.stderr)
        print("  python3 probe.py openrouter https://openrouter.ai/api/v1 \$OPENROUTER_API_KEY", file=sys.stderr)
        sys.exit(2)

    provider = sys.argv[1]
    base_url = sys.argv[2]
    api_key = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    model = sys.argv[4] if len(sys.argv) > 4 else None

    result = probe(provider, base_url, api_key=api_key, model=model)

    print(json.dumps(result, indent=2))

    if not result.get("alive"):
        sys.exit(2)
    if result.get("model_found") is False:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()