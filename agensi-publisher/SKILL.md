---
name: agensi-publisher
description: Publish AI agent skills to the Agensi marketplace end-to-end — account setup, profile, ZIP submission, admin review, updates, and handling the 8-point security scan. Works for any creator listing their first SKILL.md-based skill.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: productivity
subdomain: developer-tools
tags:
  - agensi
  - marketplace
  - publishing
  - skills
  - skil.md
  - creator
  - listing
---

# Agensi Publisher

Publish a SKILL.md-based AI agent skill to the Agensi marketplace
(agensi.io) — from account creation through submission for admin review,
then keep it updated. This guide covers the complete flow with the quirks
you'll hit along the way, so you don't have to learn them the hard way.

## When to Use

- You've built a SKILL.md-based AI agent skill and want to publish it on Agensi.
- You need to set up a creator account and complete your profile.
- Your submission got rejected (likely by the automated security scan) and you need to fix it.
- You need to update an already-listed skill without breaking it.

**Don't use for:** Creating skill content itself. Publishing to non-Agensi
platforms — other marketplaces have their own flows.

## Prerequisites

- A built skill packaged as a `.zip` (SKILL.md at root or in a subdirectory)
- A valid email address for the creator account
- A web browser you can operate manually (for Google SSO steps)

## Procedure

### Step 1: Create Your Account

1. Navigate to `https://www.agensi.io/auth`
2. Click **"Don't have an account? Sign up"**
3. Fill in a display name, email, and password
4. Click **"Create account"**
5. Check your inbox — **the verification email may not arrive** (known
   Supabase/Gmail delivery bug). If it doesn't, use **Google SSO** sign-in
   instead; it confirms the account automatically.
6. After SSO, use **"Forgot password"** to set a real password (SSO
   accounts have none by default). Follow the reset link from your email.

### Step 2: Complete Your Creator Profile

1. Go to `https://www.agensi.io/dashboard`
2. Click **"Edit profile"** under the Creator Setup checklist
3. Set your **Display Name**, write a short **Bio**, upload an **avatar**
   (square image, 512×512 recommended)
4. Click **"Save Profile"**

A complete profile matters — buyers check who made a skill before
installing it.

### Step 3: Submit a Skill

1. Go to `https://www.agensi.io/dashboard/submit`
2. **Upload your ZIP** (drag-drop or file picker). The page parses your
   frontmatter automatically — you'll see "SKILL.md found, N fields
   auto-populated."
3. **Verify the auto-filled fields**: skill name, summary, and description
   come from your frontmatter. Fix anything off before continuing.
4. Fill the **Full Description** with a clear write-up of what the skill
   does and what problem it solves.
5. Fill the **Compatibility Note** (e.g. runtime requirements).
6. Pick your **Pricing** (Free, One-time, or Subscription).
7. Click **"Submit for Review"** — a confirmation dialog opens.
8. In the dialog, click **"Submit for review"** (note: there are two submit
   buttons on the page; the dialog's is the one you want).

### Step 4: Verify Submission

1. Open your dashboard → **Creator Studio**
2. Confirm status shows **"Pending Review"** or **"In review"**
3. Admin review typically takes 24-48 hours. You'll get a notification
   when it's approved or rejected.

## Updating an Existing Skill

1. In **Creator Studio**, find your skill card and click **Update**.
2. In the dialog, upload the new ZIP (a new ZIP triggers re-approval).
3. Click **"Save & Resubmit for Review"** — note this button text differs
   from the initial-submit flow.
4. Confirm in the dialog. Your listing is temporarily UNLISTED until the
   new version is approved.

## The 8-Point Security Scan — How to Pass It

Every submission runs an automated security scan. The most common
rejection is **undeclared network access**: the scan warns on outbound
network calls (fetch, curl, requests) that aren't declared.

**If rejected**, you'll see a message like:
*"The skill attempts to access 'example.com' and 'api.other.org' via
network calls, which were explicitly removed from its declared hosts."*

Fix it in two places:

1. **In the ZIP's SKILL.md frontmatter**, declare the endpoints:
   ```yaml
   external_urls:
     - https://example.com/api
     - https://api.other.org
   permissions:
     - network
   ```
2. **In the listing's Permissions tab**, add each domain to **Allowed
   Hosts** and set File Scopes to `<your-skill-name>/**`.

Then resubmit. The scan is otherwise fair — keep secrets out of the skill,
no exfiltration patterns, no prompt injection.

## Pitfalls (learned the hard way)

- **Verification email never arrives**: Go straight to Google SSO rather
  than waiting for resend attempts.
- **State loss on page reload**: The submit form drops your uploaded ZIP on
  refresh. Do the full upload → fill → submit in one session.
- **Stale form data**: If you submit multiple skills in one session, form
  fields can pre-fill with the PREVIOUS skill's data. Always double-check
  name and summary before submitting.
- **Stale dashboard widget**: The Creator Setup checklist may show
  "Connect payouts" as incomplete even after you've connected Stripe.
  Check **Creator Studio → Payouts** for the real status ("Stripe
  Connected ... Active").
- **Permission carryover on updates**: When updating, the Permissions tab
  may still show the PREVIOUS skill's allowed hosts and file scopes.
  Remove stale entries before saving.

## Verification Checklist

- [ ] Your public profile shows at `agensi.io/creators/<your-slug>`
- [ ] Creator Studio shows your skill **Pending Review** (or **Live**)
- [ ] Permissions match what the skill actually does
- [ ] No secrets, tokens, or personal paths inside the ZIP

## Related

- Agensi marketplace: `https://www.agensi.io/skills`
- Agensi security page: `https://www.agensi.io/security`
- SKILL.md standard: open standard used by Claude Code, Codex CLI, Cursor,
  Gemini CLI, OpenCode and 20+ other agents