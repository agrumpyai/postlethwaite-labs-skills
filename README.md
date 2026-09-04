# Postlethwaite Labs — Open Source AI Agent Skills

**Practical AI agent skills for people who build and run things.**

Free, MIT-licensed SKILL.md packages built from real-world use: self-hosted AI
in production, cybersecurity operations, and single-operator automation.

## ☕ Support the work

These skills are free forever. If one of them saves you time, money, or a
late night — [**buy me a coffee**](https://buymeacoffee.com/postlethwaite) ☕

Your support funds more free skills and keeps the marketplace growing.

## 📦 Skills

| Skill | Category | Description |
|---|---|---|
| [Model Router](model-router/) | AI Agents & LLM Ops | Route AI tasks across cloud and local LLM providers with automatic fallback. GPU-agnostic detection. |
| [CISA KEV Vulnerability Monitor](cisa-kev-monitor/) | Security & Compliance | Watch the CISA Known Exploited Vulnerabilities catalog against your own stack. EPSS-enriched alerts. |
| [Daily Briefing Pipeline](hermes-briefing-pipeline/) | Productivity | Automated branded PDF briefings via cron — scrape, summarise, PDF, email. |
| [Threat Feed Aggregator](threat-feed-aggregator/) | Security & Compliance | Dedupe cyber threat news from 5 trusted sources into one clean briefing. |
| [Agensi Publisher](agensi-publisher/) | Developer Tools | Publish AI agent skills to the Agensi marketplace end-to-end. A meta-skill for creators. |
| [Update Checker](update-checker/) | Developer Tools | Check whether software updates are worth installing — release notes, security context, and a clear verdict. |
| [Chat Games](chat-games/) | Entertainment | Play 20 Questions, hangman, trivia, riddles, text adventures, and more with your agent. |
| [LLM GPU Fit](llm-gpu-fit/) | AI Agents & LLM Ops | Check if an LLM fits your GPU before downloading it — VRAM, context, and agent compatibility in one decision procedure. |
| [Local Codegen Workflow](local-codegen-workflow/) | AI Agents & LLM Ops | Generate production code with a local LLM on the GPU you already own — spec-driven, with auto model-loading and a review checklist. |

## 🚀 Get started

```bash
# Clone the repo
git clone https://github.com/agrumpyai/postlethwaite-labs-skills.git
cd postlethwaite-labs-skills

# Pick a skill, e.g. the threat feed aggregator
cd threat-feed-aggregator
python3 threat_aggregator.py --format text
```

Each skill folder contains its own `SKILL.md` (drop it into any
SKILL.md-compatible agent: Claude Code, Codex CLI, Cursor, Hermes, OpenCode,
and 20+ more), plus scripts, config examples, and README.

## 🛡️ Security

All skills are designed to be privacy-first: no telemetry, no accounts, no
third-party data storage. Where a skill calls external APIs (CISA KEV,
FIRST EPSS, public RSS feeds), the only outbound request is to the public
endpoint — no analysis or usage data is sent anywhere.

## 🛣️ Roadmap

- More skills in the security & ops space
- Paid Pro versions with deeper integrations (for those who want them)
- Community contributions welcome

## 📫 Contact

- [Agensi storefront](https://www.agensi.io/creators/postlethwaite-labs)
- [Fixify iT](https://fixifyit.co.uk)

## License

All skills are MIT-licensed unless otherwise noted. Use them freely,
modify them, sell your own versions — attribution appreciated, not required.