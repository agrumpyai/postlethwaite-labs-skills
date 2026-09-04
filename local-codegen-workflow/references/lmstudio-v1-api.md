# LM Studio v1 REST API — Model Management

LM Studio 0.4.0+ ships a native REST API at the server **root** (`/api/v1/*`),
separate from the OpenAI-compatible namespace (`/v1/*`) and the legacy v0 API
(`/api/v0/*`, which has NO model management).

## Endpoints

| Method | Path | Body | Purpose |
|---|---|---|---|
| GET | `/api/v1/models` | — | List models; each entry has `loaded_instances: []` (unloaded) or `[{id, config:{context_length,...}}]` |
| POST | `/api/v1/models/load` | `{"model": key, "context_length": N, "flash_attention": true, "echo_load_config": true}` | Load a model at a SPECIFIC context |
| POST | `/api/v1/models/unload` | `{"instance_id": key}` | Unload a model instance |

Note: `POST /api/v1/models/load` with an empty body returns
`400 {"error":{"message":"Missing required field 'model'", ...}}` — that's the
endpoint existing and validating, not a failure.

## The context-length trap (root cause of most "terminated" errors)

- A model's GGUF reports its **maximum** context (e.g. Qwen2.5-Coder-14B = 131072).
- LM Studio's default configuration and JIT loading use that max unless told
  otherwise.
- At 131K on a 16GB card: weights (~9.5GB Q4_K_M) + KV cache (~21GB) = OOM.
- Result: the model "loads", tiny requests succeed, real generations die with

```json
{"error": "terminated"}
```

**This error means OOM/wrong-context — NOT "model not loaded".** Check
`loaded_instances` before anything else.

**Fix:** request an explicit context on load. Reference values:

| GPU VRAM | Model | Safe context |
|---|---|---|
| 16GB | Qwen2.5-Coder-14B Q4_K_M | 32768 (flash attention on) |
| 12GB | Qwen2.5-Coder-14B Q4_K_M | 16384 |
| 16GB | Qwen2.5-Coder-7B | 65536+ |

## VRAM behaviour with two models

On a 16GB box, loading a second model does NOT always evict the first — LM
Studio can partially CPU-offload it. Both stay in `loaded_instances`; the
offloaded one runs slower but works. If you need guaranteed single-model
residency (e.g. swapping coder ↔ chat model), unload explicitly first.

## Reference: ensure_loaded

```python
def ensure_loaded(model: str, context_length: int | None = None,
                  flash_attention: bool = True, timeout: float = 180) -> bool:
    """Load `model` at `context_length`, swapping other models out only if
    VRAM is short. Never raises — returns bool. Polls /api/v1/models until
    loaded or timeout."""
    import httpx, time
    root = "http://localhost:1234"   # your LM Studio server
    deadline = time.monotonic() + timeout
    try:
        entries = {m["key"]: m for m in
                   httpx.get(f"{root}/api/v1/models", timeout=15).json()["models"]}
        entry = entries.get(model)
        if entry is None:
            return False
        insts = entry.get("loaded_instances", [])
        if insts:
            cur = insts[0].get("config", {}).get("context_length")
            if context_length is None or cur == context_length:
                return True
            httpx.post(f"{root}/api/v1/models/unload",
                       json={"instance_id": insts[0]["id"]}, timeout=15)
        payload = {"model": model}
        if context_length is not None:
            payload["context_length"] = context_length
        if flash_attention:
            payload["flash_attention"] = True
        r = httpx.post(f"{root}/api/v1/models/load", json=payload, timeout=timeout)
        if r.status_code != 200:
            # VRAM short — evict everything, retry once
            for m in httpx.get(f"{root}/api/v1/models", timeout=15).json()["models"]:
                for inst in m.get("loaded_instances", []):
                    httpx.post(f"{root}/api/v1/models/unload",
                               json={"instance_id": inst["id"]}, timeout=15)
            r = httpx.post(f"{root}/api/v1/models/load", json=payload, timeout=timeout)
            if r.status_code != 200:
                return False
        while time.monotonic() < deadline:
            for m in httpx.get(f"{root}/api/v1/models", timeout=15).json()["models"]:
                if m.get("key") == model and m.get("loaded_instances"):
                    return True
            time.sleep(1)
        return False
    except Exception:
        return False
```

Full working implementation (with unload-all + OpenAI-compat wiring) is
embedded in this skill's `tools/genfile.py` — see `ensure_loaded` there.
Docs: https://lmstudio.ai/docs/developer/rest (raw markdown available by
appending `.md` to any page URL).