#!/usr/bin/env python3
"""genfile.py — local LLM codegen bridge.

Sends a spec (markdown) to a local OpenAI-compatible LLM server (LM Studio,
Ollama, vLLM, etc.) and writes the generated code to a target file. Works with
ANY model — the default is a coder-class model for best results, override with
--model. The generating model produces the bulk of the code; a
human/reviewer inspects and patches afterwards.

Usage:
    python tools/genfile.py specs/db.py.md app/db.py [--model MODEL] [--max-tokens N] [--stdout]

Args:
    spec       Path to the spec markdown file (required)
    target     Output file path (required unless --stdout)
    --model    Model id to use (default: qwen2.5-coder-14b-instruct)
    --max-tokens  Max tokens in the completion (default: 8000)
    --stdout    Write to stdout instead of a file (for testing)

Env:
    LMSTUDIO_BASE_URL   Override API base (default: http://localhost:1234/v1)
    CODEGEN_CONTEXT     Context length to load the model at (default: 32768)
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import httpx

DEFAULT_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
DEFAULT_MODEL = "qwen2.5-coder-14b-instruct"
# Coder-class models fit typical 16GB GPUs at 32K context; the GGUF default
# (often 131K) OOMs the card. Adjust via CODEGEN_CONTEXT to your VRAM.
CODEGEN_CONTEXT = int(os.environ.get("CODEGEN_CONTEXT", "32768"))

SYSTEM_PROMPT = (
    "You are a senior Python developer. Write complete, production-quality, "
    "working code that exactly satisfies the spec. Output ONLY the code — no "
    "explanations, no commentary, no markdown code fences. If the spec asks for "
    "multiple files, still output a single self-contained module for the "
    "requested target unless the spec explicitly says otherwise."
)


def _root_url() -> str:
    """Derive the native API root from the OpenAI-compat base URL."""
    return DEFAULT_BASE_URL.removesuffix("/v1").rstrip("/")


def _v1_models():
    """List models via LM Studio's native v1 API (best-effort)."""
    with httpx.Client(timeout=15) as client:
        r = client.get(f"{_root_url()}/api/v1/models")
        r.raise_for_status()
        return r.json().get("models", [])


def ensure_loaded(model: str, context_length: int | None = None,
                  flash_attention: bool = True, timeout: float = 240) -> bool:
    """Best-effort: load `model` at `context_length` via LM Studio's v1 API.

    Works with LM Studio 0.4.0+. For servers without the v1 API (Ollama,
    llama.cpp, vLLM), returns False quickly and generation continues — the
    server's own JIT loading handles it (possibly with its configured context).
    Never raises. Returns True if the model is (or becomes) resident.
    """
    deadline = time.monotonic() + min(timeout, 60)  # cap so non-LMStudio servers don't hang
    try:
        entries = {m["key"]: m for m in _v1_models()}
        entry = entries.get(model)
        if entry is None:
            return False
        instances = entry.get("loaded_instances", [])
        if instances:
            current_ctx = instances[0].get("config", {}).get("context_length")
            if context_length is None or current_ctx == context_length:
                return True
            with httpx.Client(timeout=15) as client:
                client.post(f"{_root_url()}/api/v1/models/unload",
                            json={"instance_id": instances[0]["id"]})
        payload = {"model": model}
        if context_length is not None:
            payload["context_length"] = context_length
        if flash_attention:
            payload["flash_attention"] = True
        with httpx.Client(timeout=60) as client:
            r = client.post(f"{_root_url()}/api/v1/models/load", json=payload)
            if r.status_code != 200:
                return False
        while time.monotonic() < deadline:
            for m in _v1_models():
                if m.get("key") == model and m.get("loaded_instances"):
                    return True
            time.sleep(1)
        return False
    except Exception:
        return False


def extract_code(text: str) -> str:
    """Strip markdown fences if the model wrapped the code anyway."""
    t = text.strip()
    if t.startswith("```"):
        # Remove leading fence + language tag
        lines = t.splitlines()
        lines = lines[1:] if lines and lines[0].startswith("```") else lines
        # Remove trailing fence if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip() + "\n"
    return t


def generate(spec_text: str, model: str, base_url: str, max_tokens: int) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": spec_text},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "stream": False,
    }
    url = base_url.rstrip("/") + "/chat/completions"
    with httpx.Client(timeout=600) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    content = data["choices"][0]["message"]["content"]
    if not content or not content.strip():
        raise RuntimeError(f"Empty completion from model {model}")
    return extract_code(content)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a file via local OpenAI-compatible LLM server")
    ap.add_argument("spec", help="Path to spec markdown")
    ap.add_argument("target", nargs="?", help="Output file path (omit with --stdout)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.spec):
        print(f"genfile: spec not found: {args.spec}", file=sys.stderr)
        return 2
    if not args.stdout and not args.target:
        ap.error("target path required unless --stdout")

    # Auto-load the codegen model at a VRAM-safe context (LM Studio only;
    # other servers JIT-load themselves). Best-effort — never blocks generation.
    print(f"genfile: ensuring {args.model} loaded (ctx {CODEGEN_CONTEXT}) …", file=sys.stderr)
    if ensure_loaded(args.model, context_length=CODEGEN_CONTEXT, timeout=240):
        print(f"genfile: {args.model} ready.", file=sys.stderr)
    else:
        print(f"genfile: auto-load skipped or unavailable — continuing with server's own handling.",
              file=sys.stderr)

    with open(args.spec, encoding="utf-8") as f:
        spec_text = f.read()

    print(f"genfile: generating with {args.model} ...", file=sys.stderr)
    try:
        code = generate(spec_text, args.model, DEFAULT_BASE_URL, args.max_tokens)
    except (httpx.HTTPError, RuntimeError, KeyError, IndexError) as e:
        print(f"genfile: FAILED — {e}", file=sys.stderr)
        return 1

    if args.stdout:
        sys.stdout.write(code)
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(args.target)), exist_ok=True)
    with open(args.target, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"genfile: wrote {args.target} ({len(code)} chars)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())