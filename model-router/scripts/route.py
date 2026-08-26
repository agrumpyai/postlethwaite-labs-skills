#!/usr/bin/env python3
"""
model-router: route.py — Validate a full provider routing chain.

Reads a config file (JSON or YAML) and tests each provider in order,
reporting which ones are available and what models they serve.

Usage:
    python3 route.py [config_path]
    python3 route.py ~/.model-router/config.json

Exit codes:
    0 = at least one provider in chain is working
    1 = no providers in chain are working
    2 = config file not found or invalid
"""

import json
import os
import sys
from pathlib import Path

# Add scripts dir to path for sibling imports
SCRIPTS_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPTS_DIR))

import probe as probe_mod


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.model-router/config.json")


def _load_config_file(path):
    """Load config from file. Supports JSON and YAML (if PyYAML available)."""
    content = path.read_text(encoding="utf-8")

    # Try JSON first
    try:
        return json.loads(content), None
    except json.JSONDecodeError:
        pass

    # Try YAML
    try:
        import yaml
        data = yaml.safe_load(content)
        if data is not None:
            return data, None
    except ImportError:
        pass
    except yaml.YAMLError as e:
        return None, f"Invalid YAML: {e}"

    # If YAML wasn't available, suggest it
    try:
        import yaml  # noqa: F401
        return None, "Could not parse config file. Must be valid JSON or YAML."
    except ImportError:
        return None, (
            "Could not parse config file as JSON, and PyYAML is not installed. "
            "Install PyYAML (pip install pyyaml) or use a .json config file."
        )


def load_config(config_path):
    """Load and validate a config file."""
    path = Path(config_path).expanduser()

    # Also try .yaml if .json doesn't exist
    if not path.exists():
        yaml_path = path.with_suffix(".yaml")
        if yaml_path.exists():
            path = yaml_path
        yml_path = path.with_suffix(".yml")
        if not path.exists() and yml_path.exists():
            path = yml_path

    if not path.exists():
        return None, f"Config file not found: {path}"

    data, error = _load_config_file(path)
    if error:
        return None, error

    routers = data.get("routers", [])
    if not routers:
        routers = data.get("providers", data.get("chain", []))

    if not routers:
        return None, "No 'routers' list found in config"

    return routers, None


def resolve_api_key(entry):
    """
    Resolve API key from config entry.
    Priority: entry.api_key > entry.api_key_env > env var matching provider name.
    """
    key = entry.get("api_key", "")
    if key and key != "your-api-key-here":
        if key.startswith("${") and key.endswith("}"):
            env_var = key[2:-1]
            return os.environ.get(env_var, "")
        return key

    key_env = entry.get("api_key_env", "")
    if key_env:
        return os.environ.get(key_env, "")

    provider = entry.get("provider", "").lower()
    provider_env_map = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "lmstudio": "LMSTUDIO_API_KEY",
    }
    if provider in provider_env_map:
        return os.environ.get(provider_env_map[provider], "")

    return ""


def validate_chain(config_path=None):
    """Validate a full routing chain from config."""
    config_path = config_path or DEFAULT_CONFIG_PATH
    routers, error = load_config(config_path)
    if error:
        return {"status": "error", "error": error, "providers": []}

    results = []
    any_working = False

    for i, entry in enumerate(routers):
        name = entry.get("name", f"provider-{i}")
        provider = entry.get("provider", "custom")
        base_url = entry.get("base_url", "")
        model = entry.get("model", "")
        tier = entry.get("tier", "unspecified")
        api_key = resolve_api_key(entry)

        cloud_defaults = {"openrouter", "openai", "anthropic"}

        print(f"  [{i+1}/{len(routers)}] {name} ({provider}/{tier})...", end=" ", flush=True)

        if not base_url and provider in cloud_defaults:
            print("✅ cloud (no probe needed)")
            any_working = True
            results.append({
                "name": name, "provider": provider, "model": model,
                "tier": tier, "alive": True, "status": "ok",
                "note": "cloud provider — assumed alive",
            })
            continue

        if not base_url:
            print(f"❌ no base_url configured")
            results.append({
                "name": name, "provider": provider, "model": model,
                "tier": tier, "alive": False, "status": "no_base_url",
            })
            continue

        probe_result = probe_mod.probe(
            provider=provider,
            base_url=base_url,
            api_key=api_key or None,
            model=model or None,
        )

        alive = probe_result.get("alive", False)
        status = probe_result.get("status", "unknown")
        models = probe_result.get("models", [])
        model_found = probe_result.get("model_found")
        error_msg = probe_result.get("error", "")

        if alive:
            any_working = True
            if model_found is False:
                print(f"reachable, but model '{model}' not found")
            else:
                print(f"✅ alive ({len(models)} models)")
        elif "auth_error" in status:
            print(f"❌ auth error (check API key)")
        else:
            print(f"❌ {error_msg[:60]}")

        results.append({
            "name": name, "provider": provider, "model": model,
            "tier": tier, "alive": alive, "status": status,
            "models": models, "model_found": model_found, "error": error_msg,
        })

    return {
        "status": "ok" if any_working else "no_working_providers",
        "any_working": any_working,
        "total_providers": len(routers),
        "working_count": sum(1 for r in results if r["alive"]),
        "providers": results,
    }


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH

    print("╔══════════════════════════════════════════════╗")
    print("║     model-router — Chain Validation          ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"  Config: {config_path}")
    print()

    result = validate_chain(config_path)

    if result["status"] == "error":
        print(f"\n❌ Error: {result['error']}")
        sys.exit(2)

    print()
    print("── Summary ──")
    print(f"  Providers: {result['total_providers']}")
    print(f"  Working:   {result['working_count']}")
    print(f"  Failed:    {result['total_providers'] - result['working_count']}")

    if result["any_working"]:
        print("\n✅ At least one provider is working — chain is functional.")
        sys.exit(0)
    else:
        print("\n❌ No providers are working. Check your config and start services.")
        sys.exit(1)


if __name__ == "__main__":
    main()