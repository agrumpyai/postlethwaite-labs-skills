---
name: update-checker
description: Check whether software updates are worth installing — fetches latest versions, release notes, and gives a clear verdict (safe, urgent, or risky). A decision framework for any agent, not a script.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: productivity
subdomain: developer-tools
tags:
  - updates
  - version-check
  - release-notes
  - security
  - devops
  - software-maintenance
---

# Update Checker

A decision framework that teaches your AI agent how to check whether
software updates are worth installing. Give it a tool name and your
current version, and it'll research the latest release, read the
changelog, and tell you whether to update, wait, or act urgently.

**No scripts, no APIs, no maintenance.** The agent does the research
fresh every time using standard tools (web search, terminal, browser).

## When to Use

- You see a notification that an update is available and want to know
  if it's safe to install.
- You're maintaining a server or homelab and want to check if any of
  your tools have security patches.
- You want a quick weekly "update check" across your stack.
- You're evaluating whether to upgrade a critical dependency in a
  project.

## The Decision Framework

The agent follows this process for every tool you ask about:

### Step 1 — Find the Current Version

```
User: "Check if Hermes is worth updating"
Agent: "What version are you running?"
```

If you don't know, the agent can check common package managers
(`pip show`, `npm list`, `apt policy`, `docker --version`, etc.)
or ask you to run the version command.

### Step 2 — Find the Latest Version

The agent checks one or more of these sources (whichever works):

| Source | Method | Example |
|---|---|---|
| GitHub Releases | `web_search` or browser | `github.com/owner/repo/releases` |
| Official website | `web_extract` or browser | `nodejs.org/en/download` |
| Package registry | `terminal` | `pip index versions`, `npm view` |
| RSS / changelog feed | `web_extract` | Many projects publish one |

### Step 3 — Fetch the Release Notes

The agent reads the changelog between your version and the latest,
focusing on:

- **Security fixes** — CVEs, vulnerabilities patched
- **Breaking changes** — config format changes, removed features
- **Relevant features** — things that would actually matter to you
- **Bug fixes** — especially if you're hitting any of them

### Step 4 — Give a Verdict

The agent presents a concise, colour-coded verdict:

```
🟢 Hermes v0.20.4 → v0.20.5
  Patch release, 1 day behind. Cron memory improvements, bug fixes.
  Verdict: ✅ Worth it — low risk, no breaking changes.

🟡 Docker Engine 27.0.0 → 27.3.1
  3 minor versions behind. Security fix + new features.
  Verdict: ⚠️ Worth it — check compose file compatibility.

🔴 OpenSSL 3.0.13 → 3.0.15
  Security patch. CVE-2026-XXXX fixes active exploitation.
  Verdict: 🚨 Urgent — install now.
```

### Step 5 — Optional: Install

If the verdict is positive, the agent can offer to run the appropriate
update command (`pip install -U`, `apt upgrade`, `npm update`, etc.).

## Example Interactions

### Single tool check

```
You: Check if I should update Ollama. I'm on 0.14.0.
Agent: [Searches GitHub releases, reads changelog]

🟡 Ollama 0.14.0 → 0.16.2
  Two minor versions behind. Major: new vision API, Qwen3.5 support,
  fixed a memory leak in long-running sessions.
  Verdict: ⚠️ Worth it — no breaking changes in the CLI.
  Run: `curl -fsSL https://ollama.com/install.sh | sh`
```

### Full stack audit

```
You: Check my self-hosted stack for updates. I'm running:
  Hermes v0.20.4, Ollama 0.14.0, LM Studio 0.3.4, Docker 27.0.0,
  Ubuntu 24.04, Python 3.11.15

Agent: [Checks each one, fetches release notes, compiles report]

🟢 Hermes  → v0.20.5  ✅ Safe patch
🟡 Ollama  → v0.16.2  ⚠️ Worth it, new features
🟢 Docker  → v27.3.1  ⚠️ Security fixes, check compose compat
🔴 Ubuntu  → 24.04.1  ✅ Already on latest LTS
🟢 Python  → 3.11.15  ✅ Latest 3.11
```

## Tips

- **Be specific** about your current version — "I'm on Hermes 0.20.4"
  is better than "check for updates."
- **For GitHub-hosted tools**, the agent can usually find the latest
  release via web search or browser.
- **For self-hosted tools** (Ollama, LM Studio, etc.), the agent might
  need to check the website or GitHub releases manually.
- **If the agent can't find the version**, try giving it the exact
  project URL or GitHub repo.

## Pitfalls

- **Some projects don't tag releases cleanly** — the agent may need to
  check the commit log or npm/PyPI for the real latest version.
- **Breaking changes aren't always documented** — the agent should
  flag "major version bump" as a yellow flag by default.
- **Security advisories are sometimes published separately** from
  release notes. The agent should check the project's security page
  or CVE database if the update mentions a security fix.
- **The agent has no access to your private repos** — this works for
  public software only.

## Privacy

The agent only fetches public information: GitHub releases, official
websites, and package registries. No data about your system or
installed software leaves your machine beyond what you explicitly
tell the agent. No telemetry, no accounts.