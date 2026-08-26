# Update Checker

A decision framework for your AI agent that checks whether software
updates are worth installing — release notes, security context, and
a clear verdict.

## Why this exists

You see an update notification. You don't know if it's a critical
security patch, a risky breaking change, or just a minor bump. You
spend 10 minutes reading release notes, checking forums, and trying
to decide.

This skill teaches your agent to do that research for you.

## How it works

1. Tell the agent what you're running and what version
2. The agent checks GitHub releases, websites, and package registries
3. It reads the changelog and flags security fixes, breaking changes,
   and relevant features
4. It gives you a clear verdict: ✅ Worth it / ⚠️ Check first / 🚨 Urgent

No scripts, no APIs, no maintenance. The agent does the work fresh
every time.

## Quick start

```
You: Check if I should update Ollama. I'm on 0.14.0.
Agent: [does the research]
🟡 Ollama 0.14.0 → 0.16.2 — New vision API, Qwen3.5 support.
Verdict: ⚠️ Worth it, no breaking changes.
```

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The decision framework — drop into any SKILL.md-compatible agent |

## Privacy

Only public information is fetched. No telemetry, no accounts.

## License

MIT — use it freely.

## Support

If this saves you time, consider [buying me a coffee](https://buymeacoffee.com/postlethwaite).