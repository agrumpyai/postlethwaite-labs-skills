#!/usr/bin/env python3
"""
model-router: discover.py — Auto-detect GPU hardware and local model providers.

Vendor-agnostic GPU detection (NVIDIA, AMD, Intel, Apple Silicon).
Provider-agnostic endpoint scanning (Ollama, LM Studio, llama.cpp, vLLM, etc.).

Usage:
    python3 discover.py          # Run all detection
    python3 discover.py --gpu    # GPU only
    python3 discover.py --local  # Local providers only

Outputs YAML-ready config to stdout. No external dependencies — stdlib only.
"""

import json
import os
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request


# ── GPU Detection (vendor-agnostic) ──────────────────────────────────────────

def _run(cmd, timeout=10):
    """Run a command, return (success: bool, stdout: str, stderr: str)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired, OSError):
        return False, "", ""


def detect_nvidia():
    """Detect NVIDIA GPUs via nvidia-smi."""
    ok, out, _ = _run([
        "nvidia-smi",
        "--query-gpu=index,name,memory.total,driver_version,temperature.gpu",
        "--format=csv,noheader,nounits",
    ])
    if not ok or not out:
        return None
    gpus = []
    for line in out.strip().split("\n"):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5:
            gpus.append({
                "vendor": "nvidia",
                "index": parts[0],
                "name": parts[1],
                "vram_gb": _parse_vram(parts[2]),
                "driver": parts[3],
                "temp_c": parts[4],
            })
        elif len(parts) >= 3:
            gpus.append({
                "vendor": "nvidia",
                "index": parts[0],
                "name": parts[1],
                "vram_gb": _parse_vram(parts[2]),
            })
    return gpus if gpus else None


def detect_amd_rocm():
    """Detect AMD GPUs via rocm-smi."""
    ok, out, _ = _run(["rocm-smi", "--showhw"])
    if not ok or not out:
        return None
    gpus = []
    for line in out.split("\n"):
        m = re.search(r'GPU\s*(\d+)\s*:\s*(.+)', line)
        if m:
            gpus.append({
                "vendor": "amd",
                "index": m.group(1).strip(),
                "name": m.group(2).strip(),
            })
    return gpus if gpus else None


def detect_amd_smi():
    """Detect AMD GPUs via amd-smi (newer AMD tooling)."""
    ok, out, _ = _run(["amd-smi", "static"])
    if not ok or not out:
        return None
    gpus = []
    for block in out.split("\n\n"):
        name = ""
        for line in block.split("\n"):
            if "Name" in line or "Device" in line:
                name = line.split(":")[-1].strip()
        if name:
            gpus.append({"vendor": "amd", "name": name})
    return gpus if gpus else None


def detect_intel():
    """Detect Intel GPUs via xpu-smi."""
    ok, out, _ = _run(["xpu-smi", "discovery"])
    if not ok or not out:
        return None
    gpus = []
    for line in out.split("\n"):
        if "Device" in line and ("GPU" in line or "XPU" in line):
            gpus.append({
                "vendor": "intel",
                "name": line.strip(),
            })
    return gpus if gpus else None


def detect_apple():
    """Detect Apple Silicon via sysctl."""
    ok, out, _ = _run(["sysctl", "-n", "hw.perflevel0.name"])
    if ok and out:
        return [{"vendor": "apple", "name": out.strip()}]
    # Fallback: check model identifier
    ok2, out2, _ = _run(["sysctl", "-n", "hw.model"])
    if ok2 and out2 and ("Mac" in out2 or "Apple" in out2):
        return [{"vendor": "apple", "name": out2.strip()}]
    return None


def detect_gpu():
    """Detect GPU from any vendor. Returns list of dicts or None."""
    detectors = [
        ("nvidia", detect_nvidia),
        ("amd_rocm", detect_amd_rocm),
        ("amd_smi", detect_amd_smi),
        ("intel", detect_intel),
        ("apple", detect_apple),
    ]
    for vendor_name, detector in detectors:
        try:
            result = detector()
            if result:
                return result
        except Exception:
            continue
    return None


def _parse_vram(s):
    """Parse VRAM string to GB float."""
    try:
        return round(float(s.strip().replace(" MiB", "").replace(" MB", "")) / 1024, 1)
    except (ValueError, AttributeError):
        try:
            return float(s.strip().replace("GB", "").strip())
        except (ValueError, AttributeError):
            return None


# ── Local Provider Detection ─────────────────────────────────────────────────

def _probe_url(url, timeout=5):
    """Probe a URL. Returns (success: bool, status: str, data: dict)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "model-router/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", "replace")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
            return True, str(status), data
    except urllib.error.HTTPError as e:
        return False, str(e.code), {}
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, "unreachable", {}


def detect_ollama():
    """Detect Ollama at localhost:11434."""
    ok, status, data = _probe_url("http://localhost:11434/api/tags")
    if not ok:
        return None
    models = []
    for model in data.get("models", []):
        name = model.get("name", "unknown")
        models.append(name)
    return {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "detected": True,
        "models": models,
        "model_count": len(models),
    }


def detect_lmstudio():
    """Detect LM Studio at localhost:1234/v1/models."""
    ok, status, data = _probe_url("http://localhost:1234/v1/models")
    if not ok:
        return None
    models = []
    for model in data.get("data", []):
        mid = model.get("id", model.get("key", "unknown"))
        if mid != "unknown":
            models.append(mid)
    return {
        "provider": "lmstudio",
        "base_url": "http://localhost:1234/v1",
        "detected": True,
        "models": models,
        "model_count": len(models),
    }


def detect_llamacpp():
    """Detect llama.cpp server at localhost:8080/v1/models."""
    ok, status, data = _probe_url("http://localhost:8080/v1/models")
    if not ok:
        return None
    models = []
    for model in data.get("data", []):
        mid = model.get("id", "unknown")
        if mid != "unknown":
            models.append(mid)
    return {
        "provider": "llamacpp",
        "base_url": "http://localhost:8080/v1",
        "detected": True,
        "models": models,
        "model_count": len(models),
    }


def detect_vllm():
    """Detect vLLM server at localhost:8000/v1/models."""
    ok, status, data = _probe_url("http://localhost:8000/v1/models")
    if not ok:
        return None
    models = []
    for model in data.get("data", []):
        mid = model.get("id", "unknown")
        if mid != "unknown":
            models.append(mid)
    return {
        "provider": "vllm",
        "base_url": "http://localhost:8000/v1",
        "detected": True,
        "models": models,
        "model_count": len(models),
    }


def detect_local_providers():
    """Detect all local model providers. Returns list of dicts."""
    detectors = [
        ("Ollama", detect_ollama),
        ("LM Studio", detect_lmstudio),
        ("llama.cpp", detect_llamacpp),
        ("vLLM", detect_vllm),
    ]
    found = []
    for name, detector in detectors:
        try:
            result = detector()
            if result:
                found.append(result)
        except Exception:
            continue
    return found


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="model-router: detect GPU and local model providers"
    )
    parser.add_argument("--gpu", action="store_true", help="GPU detection only")
    parser.add_argument("--local", action="store_true", help="Local providers only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = {}

    if not args.local:
        gpu = detect_gpu()
        if gpu:
            result["gpu"] = gpu
        else:
            result["gpu"] = None
            result["gpu_message"] = (
                "No GPU detected. This is fine — the skill works in CPU-only "
                "or cloud-only mode. Install GPU drivers (nvidia-smi, rocm-smi, "
                "xpu-smi) to enable GPU detection."
            )

    if not args.gpu:
        providers = detect_local_providers()
        result["local_providers"] = providers
        if not providers:
            result["local_message"] = (
                "No local model providers detected. Start Ollama, LM Studio, "
                "llama.cpp, or vLLM on this machine and re-run discovery."
            )

    if args.json:
        print(json.dumps(result, indent=2))
        return

    # ── Human-readable output ──
    print("╔════════════════════════════════════════════╗")
    print("║     model-router — Discovery Results      ║")
    print("╚════════════════════════════════════════════╝")
    print()

    if not args.local:
        print("── GPU ──")
        if result.get("gpu"):
            for gpu in result["gpu"]:
                name = gpu.get("name", "Unknown")
                vendor = gpu.get("vendor", "unknown")
                vram = gpu.get("vram_gb", "?")
                print(f"  {vendor.upper()}: {name}  ({vram} GB VRAM)")
        else:
            print("  " + result.get("gpu_message", "No GPU detected."))
        print()

    if not args.gpu:
        print("── Local Providers ──")
        if result.get("local_providers"):
            for p in result["local_providers"]:
                name = p.get("provider", "unknown")
                url = p.get("base_url", "")
                count = p.get("model_count", 0)
                models = p.get("models", [])
                print(f"  ✅ {name} — {url}  ({count} models loaded)")
                if models:
                    for m in models[:5]:
                        print(f"       • {m}")
                    if len(models) > 5:
                        print(f"       ... and {len(models) - 5} more")
                print()
        else:
            print("  " + result.get("local_message", "No providers found."))
        print()

    # ── Starter config hint ──
    print("── Next Steps ──")
    print("  Save this config to ~/.model-router/config.yaml:")
    print()
    _print_starter_config(result)
    print()


def _print_starter_config(result):
    """Print a starter YAML config based on discovery results."""
    print("  routers:")
    print("    - name: primary-cloud")
    print("      provider: openrouter")
    print("      model: your-cloud-model")
    print("      tier: cloud")
    print("      # api_key: from OPENROUTER_API_KEY env var")
    print()

    for p in result.get("local_providers", []):
        provider = p.get("provider", "custom")
        url = p.get("base_url", "http://localhost:11434")
        models = p.get("models", [])
        model_name = models[0] if models else "your-model"
        print(f"    - name: local-{provider}")
        print(f"      provider: {provider}")
        print(f"      model: {model_name}")
        print(f"      base_url: {url}")
        print(f"      tier: local")
        print()


if __name__ == "__main__":
    main()