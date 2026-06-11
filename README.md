# Biohacking Field Notes — Content System

Automated evidence-based biohacking content by **Kai Mercer**.

Publishes to **Medium**, **Substack**, and **Vocal Media** via GitHub Actions — 3x per week.

---

## Architecture

Three-agent pipeline:

1. **Agent 1 — Scientific Reviewer**: Researches the topic, classifies evidence confidence (HIGH / MODERATE / LOW), identifies open questions and risk profile
2. **Agent 2 — Editorial (Kai Mercer)**: Writes the full article in Kai's voice, weaving in confidence ratings and personal framing
3. **Agent 3 — SEO Reviewer**: Validates metadata, adds FAQ section, improves featured snippet potential

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/biohacking-content
cd biohacking-content
```

### 2. GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Required | Description |
|--------|----------|-------------|
| `GROQ_API_KEY` | ✅ Recommended | Free at console.groq.com |
| `GEMINI_API_KEY` | Fallback | Google AI Studio |
| `MEDIUM_TOKEN` | For Medium | medium.com/me/settings → Integration tokens |
| `MEDIUM_USER_ID` | Optional | Auto-fetched from token |
| `SUBSTACK_URL` | For Substack | e.g. https://kaimercer.substack.com |
| `SUBSTACK_EMAIL` | For Substack | Your Substack login email |
| `SUBSTACK_PASSWORD` | For Substack | Your Substack password |
| `VOCAL_EMAIL` | For Vocal Media | Your Vocal login email |
| `VOCAL_PASSWORD` | For Vocal Media | Your Vocal password |

### 3. Getting your Medium Integration Token

1. Go to medium.com → your profile → Settings
2. Scroll to **Integration tokens**
3. Generate token → copy to GitHub Secret as `MEDIUM_TOKEN`

### 4. Creating your Substack

1. Go to substack.com → create publication
2. Name it "Biohacking Field Notes" (or your choice)
3. Add the URL, email, and password to GitHub Secrets

### 5. Creating your Vocal Media account

1. Go to vocal.media → Sign up
2. Go to your profile → Settings → verify your email
3. Add `VOCAL_EMAIL` and `VOCAL_PASSWORD` to GitHub Secrets
4. **Note:** Vocal reviews new stories before publishing — first few posts may take 24-48h

### 6. Enable GitHub Actions write permission

Go to **Settings → Actions → General → Workflow permissions**
Select **Read and write permissions** → Save

---

## Run manually

```bash
pip install requests python-dotenv
# create .env with your keys
python biohack_bot.py
```

---

## Schedule

Runs Monday, Wednesday, Friday at 10:00 UTC.

To change: edit `.github/workflows/biohack.yml` → `cron` line.

---

## State files

- `biohack_state.json` — post history, dates
- `biohack_used_keywords.txt` — prevents keyword repetition (resets after full cycle)

---

## Content strategy

52 keywords across: sleep, cognitive performance, longevity, metabolic health, stress/HRV, gut microbiome, light/environment, tracking, counter-intuitive takes.

High-engagement counter-intuitive topics (bonus scoring):
- "why most nootropics dont work for most people"
- "biohacking mistakes that backfire science"
- "sleep tracking anxiety paradox research"

---

## Kai Mercer persona

Former software engineer. Burnout at 34. 5 years studying the research.
Spent $40k testing protocols. Writes because the biohacking space is full of hype.

Voice: skeptical, rigorous, honest about uncertainty, never sensationalist.
