"""
Biohacking Content Autopublisher
Kai Mercer persona — evidence-based biohacking content.
Publishes to Medium, Substack, and Vocal Media via GitHub Actions.

Three-agent review system: Scientific + Editorial + SEO.
"""

import requests
import json
import random
import os
import datetime
import time
import re
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# ENV
# ---------------------------------------------------------------------------
GROQ_API_KEY        = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY", "")
MEDIUM_TOKEN        = os.environ.get("MEDIUM_TOKEN", "")
MEDIUM_USER_ID      = os.environ.get("MEDIUM_USER_ID", "")
SUBSTACK_URL        = os.environ.get("SUBSTACK_URL", "")        # e.g. https://kaimercer.substack.com
SUBSTACK_EMAIL      = os.environ.get("SUBSTACK_EMAIL", "")
SUBSTACK_PASSWORD   = os.environ.get("SUBSTACK_PASSWORD", "")
VOCAL_EMAIL         = os.environ.get("VOCAL_EMAIL", "")
VOCAL_PASSWORD      = os.environ.get("VOCAL_PASSWORD", "")

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
STATE_FILE         = "biohack_state.json"
USED_KEYWORDS_FILE = "biohack_used_keywords.txt"

# ---------------------------------------------------------------------------
# SECTION 1 — KEYWORDS
# ---------------------------------------------------------------------------
keywords = [
    # Sleep — high traffic, strong evidence base
    "sleep optimization science backed methods",
    "how to fix sleep quality with light exposure",
    "circadian rhythm hacking practical guide",
    "sleep deprivation cognitive effects research",
    "polyphasic sleep evidence review",
    "magnesium glycinate sleep does it work",
    "temperature and sleep quality science",
    "chronotype optimization morning vs night person",

    # Cognitive performance
    "nootropics evidence based review 2025",
    "lion's mane mushroom cognitive benefits research",
    "caffeine and l theanine stack science",
    "intermittent fasting brain performance studies",
    "cold exposure cognitive benefits evidence",
    "breathwork and focus wim hof method science",
    "dopamine detox real science or pseudoscience",
    "flow state neuroscience how to trigger it",

    # Longevity
    "nad+ supplementation longevity research 2025",
    "rapamycin longevity evidence risks",
    "caloric restriction longevity what research says",
    "autophagy fasting how long to trigger it",
    "telomere length lifestyle factors science",
    "blue zones diet longevity research",
    "resveratrol longevity hype vs evidence",
    "metformin anti aging research overview",

    # Metabolic health
    "continuous glucose monitor non diabetic worth it",
    "time restricted eating metabolic benefits",
    "zone 2 cardio metabolic health science",
    "vo2 max longevity predictor research",
    "high intensity interval training fat loss evidence",
    "cold plunge metabolic effects research",
    "sauna cardiovascular benefits research",
    "insulin sensitivity how to improve naturally",

    # Stress and nervous system
    "hrv heart rate variability optimization guide",
    "cortisol biohacking stress reduction science",
    "ashwagandha stress evidence based review",
    "meditation neuroplasticity research evidence",
    "box breathing parasympathetic nervous system",
    "vagus nerve stimulation evidence methods",

    # Gut microbiome
    "gut microbiome cognitive performance connection",
    "probiotics mental health research 2025",
    "fiber diversity gut health science",
    "fermented foods microbiome evidence",

    # Light and environment
    "red light therapy evidence based review",
    "blue light blocking glasses science",
    "grounding earthing health claims evidence",
    "morning sunlight cortisol awakening response",

    # Tracking and testing
    "biomarkers worth tracking for longevity",
    "at home blood testing what actually matters",
    "continuous glucose monitor insights non diabetic",
    "oura ring accuracy research review",

    # Counter-intuitive / high engagement
    "biohacking mistakes that backfire science",
    "supplements most people waste money on",
    "why most nootropics dont work for most people",
    "overtraining signs your optimization is hurting you",
    "sleep tracking anxiety paradox research",
    "why cold showers are overhyped evidence",
]

HIGH_ENGAGEMENT_INDEXES = list(range(46, 52))

# ---------------------------------------------------------------------------
# SECTION 2 — TRUSTED SOURCES
# ---------------------------------------------------------------------------
science_sources = [
    {"name": "PubMed / NIH",          "url": "https://pubmed.ncbi.nlm.nih.gov"},
    {"name": "Nature",                 "url": "https://www.nature.com"},
    {"name": "Cell Metabolism",        "url": "https://www.cell.com/cell-metabolism"},
    {"name": "Journal of Physiology",  "url": "https://physoc.onlinelibrary.wiley.com"},
    {"name": "Sleep Foundation",       "url": "https://www.sleepfoundation.org"},
    {"name": "Examine.com",            "url": "https://examine.com"},
    {"name": "Harvard Health",         "url": "https://www.health.harvard.edu"},
    {"name": "Cleveland Clinic",       "url": "https://my.clevelandclinic.org"},
    {"name": "Andrew Huberman Lab",    "url": "https://www.hubermanlab.com"},
    {"name": "Peter Attia MD",         "url": "https://peterattiamd.com"},
]


def pick_sources(keyword):
    kw = keyword.lower()
    if any(w in kw for w in ["sleep", "circadian", "chronotype"]):
        names = ["Sleep Foundation", "PubMed / NIH", "Andrew Huberman Lab"]
    elif any(w in kw for w in ["nootropic", "lion", "supplement", "nad", "resveratrol", "metformin", "ashwagandha"]):
        names = ["Examine.com", "PubMed / NIH", "Peter Attia MD"]
    elif any(w in kw for w in ["longevity", "telomere", "autophagy", "caloric", "rapamycin"]):
        names = ["PubMed / NIH", "Cell Metabolism", "Peter Attia MD"]
    elif any(w in kw for w in ["glucose", "insulin", "metabolic", "fasting", "cardio", "hiit", "vo2"]):
        names = ["PubMed / NIH", "Cell Metabolism", "Cleveland Clinic"]
    elif any(w in kw for w in ["hrv", "cortisol", "stress", "vagus", "breathing", "meditation"]):
        names = ["PubMed / NIH", "Andrew Huberman Lab", "Harvard Health"]
    elif any(w in kw for w in ["gut", "microbiome", "probiotic", "fiber"]):
        names = ["PubMed / NIH", "Nature", "Examine.com"]
    elif any(w in kw for w in ["red light", "blue light", "grounding", "sunlight"]):
        names = ["PubMed / NIH", "Andrew Huberman Lab", "Cleveland Clinic"]
    else:
        names = ["PubMed / NIH", "Harvard Health", "Examine.com"]

    result = []
    for n in names:
        for s in science_sources:
            if n.lower() in s["name"].lower():
                result.append(s)
                break
    while len(result) < 3:
        for s in science_sources:
            if s not in result:
                result.append(s)
            if len(result) == 3:
                break
    return result[:3]


# ---------------------------------------------------------------------------
# SECTION 3 — SCHEDULE
# ---------------------------------------------------------------------------
def _today_iso():
    return datetime.date.today().isoformat()


def _read_state():
    if not os.path.exists(STATE_FILE):
        state = {"start_date": _today_iso(), "week": 1, "posts_log": [], "posts_today": []}
        _write_state(state)
        return state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        state = {"start_date": _today_iso(), "week": 1, "posts_log": [], "posts_today": []}
        _write_state(state)
        return state


def _write_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def should_post_now():
    state = _read_state()
    today = _today_iso()
    count_today = sum(1 for d in state.get("posts_today", []) if d == today)
    # 3x per week cadence: post if under daily limit
    limit = 1
    if count_today < limit:
        return True
    print("[SCHEDULE] Limit reached for today.")
    return False


# ---------------------------------------------------------------------------
# SECTION 4 — KEYWORD SELECTION
# ---------------------------------------------------------------------------
def _kw_words(keyword):
    return [w for w in re.split(r"\W+", keyword.lower()) if len(w) > 2]


def get_reddit_signal(keyword):
    """Score keyword against r/biohacking and r/longevity top posts."""
    try:
        subreddits = ["biohacking", "longevity", "nootropics", "sleep", "intermittentfasting"]
        kw_words = set(_kw_words(keyword))
        matches = 0
        for sub in subreddits:
            try:
                r = requests.get(
                    f"https://www.reddit.com/r/{sub}/top.json",
                    params={"limit": 10, "t": "week"},
                    headers={"User-Agent": "BiohackBot/1.0"},
                    timeout=10,
                )
                if r.status_code != 200:
                    continue
                for post in r.json().get("data", {}).get("children", []):
                    pdata = post.get("data", {})
                    if pdata.get("score", 0) < 50:
                        continue
                    title_words = set(_kw_words(pdata.get("title", "")))
                    if kw_words & title_words:
                        matches += 1
            except Exception:
                continue
        return min(matches, 3)
    except Exception:
        return 0


def _read_used():
    if not os.path.exists(USED_KEYWORDS_FILE):
        open(USED_KEYWORDS_FILE, "w", encoding="utf-8").close()
        return []
    with open(USED_KEYWORDS_FILE, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def _mark_used(kw):
    with open(USED_KEYWORDS_FILE, "a", encoding="utf-8") as f:
        f.write(kw + "\n")


def get_best_keyword():
    used = _read_used()
    if len(used) >= len(keywords):
        open(USED_KEYWORDS_FILE, "w", encoding="utf-8").close()
        used = []

    scored = []
    for i, kw in enumerate(keywords):
        if kw in used:
            continue
        reddit = get_reddit_signal(kw)
        unused_bonus = 1
        engagement_bonus = 1 if i in HIGH_ENGAGEMENT_INDEXES else 0
        scored.append((kw, reddit + unused_bonus + engagement_bonus))

    if not scored:
        scored = [(kw, 0) for kw in keywords]

    scored.sort(key=lambda x: x[1], reverse=True)
    print("Top 3 keyword candidates:")
    for kw, s in scored[:3]:
        print(f"  [{s}] {kw}")

    top = scored[0][1]
    tied = [kw for kw, s in scored if s == top]
    chosen = random.choice(tied) if len(tied) > 1 else scored[0][0]
    _mark_used(chosen)
    return chosen


# ---------------------------------------------------------------------------
# SECTION 5 — LLM CALL
# ---------------------------------------------------------------------------
def call_llm(prompt, temperature=0.7, max_tokens=4000):
    """Groq primary, Gemini fallback."""
    if GROQ_API_KEY:
        url = "https://api.groq.com/openai/v1/chat/completions"
        body = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": min(temperature, 1.0),
            "max_tokens": max_tokens,
        }
        for attempt in range(3):
            try:
                r = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json=body,
                    timeout=120,
                )
                if r.status_code == 429:
                    wait = 30 * (attempt + 1)
                    print(f"Groq rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                text = r.json()["choices"][0]["message"]["content"]
                if not text:
                    raise RuntimeError("Empty response")
                return text
            except Exception as e:
                if attempt < 2:
                    print(f"Groq attempt {attempt+1} failed: {e}. Retrying...")
                    time.sleep(5 * (attempt + 1))
                    continue
                raise Exception(f"Groq failed: {e}")

    if not GEMINI_API_KEY:
        raise Exception("No LLM API key. Set GROQ_API_KEY or GEMINI_API_KEY.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    for attempt in range(3):
        try:
            r = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
                },
                timeout=120,
            )
            if r.status_code == 429:
                time.sleep(90 * (2 ** attempt))
                continue
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            if not text:
                raise RuntimeError("Empty response")
            return text
        except Exception as e:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise Exception(f"Gemini failed: {e}")


# ---------------------------------------------------------------------------
# SECTION 6 — RESEARCH PASS (Agent 1: Scientific Reviewer)
# ---------------------------------------------------------------------------
def research_pass(keyword, sources):
    sources_md = "\n".join([f'- [{s["name"]}]({s["url"]})' for s in sources])
    prompt = f"""You are Agent 1: Scientific Reviewer for a biohacking publication.

Topic: "{keyword}"

Your job is to produce a rigorous scientific fact-file. This will be used as the backbone of an article.

Deliver EXACTLY these sections as structured bullet points:

1. EVIDENCE TIER
   What is the strongest evidence type available for this topic?
   (Systematic Review / RCT / Cohort Study / Expert Consensus / Weak/Anecdotal)
   State this honestly. If evidence is mixed, say so.

2. KEY FINDINGS (4-6 findings)
   Each finding must include:
   - The specific claim
   - Study type supporting it
   - Sample size if known
   - Effect size or magnitude (small/moderate/large)
   - Source: {sources_md}

3. WHAT WE DON'T KNOW YET
   3-4 genuine open questions in the research.
   What would a rigorous scientist want to know that we currently can't answer?

4. COUNTERINTUITIVE FINDING
   One thing the research shows that contradicts popular belief about this topic.
   Must be sourced. Must be specific.

5. PRACTICAL THRESHOLD
   At what dose/frequency/duration does evidence suggest benefit begins?
   If unknown, state clearly: "No established threshold in current literature."

6. RISK PROFILE
   Who should approach this with caution or avoid it entirely?
   Base only on published evidence, not speculation.

7. CONFIDENCE RATINGS
   Rate each key finding:
   HIGH CONFIDENCE — replicated, large samples, strong effect
   MODERATE CONFIDENCE — limited replications or mixed results
   LOW CONFIDENCE — single studies, small samples, or theoretical

Be ruthlessly honest. If something is mostly hype with weak evidence, say so directly.
Length: 400-600 words."""
    return call_llm(prompt, temperature=0.2, max_tokens=1500)


# ---------------------------------------------------------------------------
# SECTION 7 — ARTICLE PASS (Agent 2: Editorial + Kai Mercer persona)
# ---------------------------------------------------------------------------
def write_article(research, keyword, sources):
    sources_lines = "\n".join([f'[{s["name"]}]({s["url"]})' for s in sources])
    prompt = f"""You are Kai Mercer. Here is exactly who you are.

BACKGROUND:
- 38 years old, former software engineer at a mid-size fintech company
- At 34, had a severe burnout: 6 months unable to work, brain fog, chronic fatigue
- That crisis sent him down a 5-year rabbit hole of neuroscience, longevity research,
  and human performance — not to become an influencer, but to fix himself
- He spent $40,000 testing protocols on himself. Some worked. Most didn't.
- He is NOT a doctor. He is NOT a PhD. He is relentlessly honest about this.
- He writes because the information landscape in biohacking is overwhelmingly full of
  hype, bad science, and people selling things — and he wasted years following that noise

KAI'S RELATIONSHIP WITH EVIDENCE:
- He trusts systematic reviews and RCTs. He is deeply skeptical of single studies.
- He regularly changes his mind when evidence changes. He says so in writing.
- He distinguishes between "interesting preliminary finding" and "established fact"
- He never extrapolates from animal studies to humans without flagging it
- He has tried almost everything he writes about. He reports honestly when it didn't work for him
- He knows his N=1 is not data. He says this explicitly.

KAI'S WRITING VOICE:
- Opens with a specific moment, failure, or surprising finding — never a definition
- Uses "I" sparingly but precisely — only when his personal experience adds real context
- Short sentences when making a point. Longer when building context.
- Never uses: "game changer", "revolutionary", "unlock your potential", "optimize your life"
- Never uses: "In today's world", "It's worth noting", "Let's dive in"
- Always names uncertainty: "The evidence here is thin", "I'm not convinced", "This might not apply to you"
- Cites sources inline, naturally: "A 2023 meta-analysis in Nature found..." not footnotes
- Ends each section moving forward — never summarizing what he just said

WRITE A COMPLETE ARTICLE about: "{keyword}"

SCIENTIFIC BACKBONE (use everything here):
{research}

CITE THESE SOURCES naturally inline:
{sources_lines}

REQUIRED FORMAT:

[SEO_TITLE]: compelling, contains keyword, 55-60 characters
[META]: 150-160 characters, contains keyword, reads like a human wrote it
[SLUG]: url-friendly-slug-here
[TAGS]: tag1, tag2, tag3, tag4, tag5

# [H1 — Kai-style, specific, slightly contrarian, 8-12 words]

[Opening: 3-5 sentences. Personal moment or surprising research finding.
No setup. No "in this article I will..." Just start.]

## [H2 — contains keyword, sets up the evidence review]
[250-300 words — what the research actually shows, confidence ratings woven in,
one specific study cited naturally, one thing that surprised Kai]

## [H2 — the gap between popular belief and evidence]
[230-270 words — the counterintuitive finding, what people get wrong,
Kai's honest assessment including where he changed his mind]

## [H2 — what the evidence says about practical application]
[200-240 words — specific protocols with doses/timing/duration from research,
explicit about what has evidence vs what is extrapolation]

## [H2 — risks, caveats, and who this isn't for]
[180-220 words — honest risk profile, who should avoid it,
Kai's personal caveats]

## What We Still Don't Know
[150-180 words — genuine open questions, what future research would change Kai's view,
ends with one honest uncertainty that makes the reader think]

[LEAD_MAGNET_1]
After the introduction, insert a subtle CTA:
"[If you want my personal tracking template for [topic], it's in the free Biohacking Field Notes newsletter — link at the end.]"

[LEAD_MAGNET_2]
After the third H2, insert:
"[I cover protocol updates and study breakdowns every week in Biohacking Field Notes — free, no upsells, just research.]"

[LEAD_MAGNET_3]
After final section, insert a closing CTA linking to Substack.

ABSOLUTE RULES:
- Minimum 1,800 words
- Every claim must match confidence rating from research pass
- Never present LOW CONFIDENCE findings as established facts
- No bullet point lists — paragraphs only
- Keyword "{keyword}" in H1, opening, and at least 2 H2s
- Final sentence should be honest and slightly uncomfortable, not motivational
- Include FAQ section with 4 questions at the end"""

    raw = call_llm(prompt, temperature=0.85, max_tokens=5000)
    return raw


# ---------------------------------------------------------------------------
# SECTION 8 — SEO PASS (Agent 3: SEO Reviewer)
# ---------------------------------------------------------------------------
def seo_pass(article_raw, keyword):
    prompt = f"""You are Agent 3: SEO Reviewer.

Review this biohacking article draft about "{keyword}" and return an improved version.

Your tasks:
1. Verify SEO_TITLE is 55-60 chars and contains the keyword
2. Verify META is 150-160 chars and reads naturally
3. Verify SLUG is clean (lowercase, hyphens, no stop words)
4. Verify H2s contain semantic keywords naturally
5. Add a FAQ section if missing (4 questions, answers 40-60 words each)
   Format:
   ## Frequently Asked Questions
   **Q: [question]**
   [answer]
6. Verify keyword appears naturally in first 100 words
7. Ensure internal structure supports featured snippet potential
   (clear direct answers near the top of relevant sections)

Do NOT change Kai's voice or add hype language.
Do NOT change any confidence ratings or scientific claims.
Return the full improved article — same format, same structure.

ARTICLE TO REVIEW:
{article_raw}"""

    return call_llm(prompt, temperature=0.3, max_tokens=5500)


# ---------------------------------------------------------------------------
# SECTION 9 — PARSE ARTICLE
# ---------------------------------------------------------------------------
def parse_article(raw):
    """Extract metadata and content from raw LLM output."""
    def extract(pattern, text, default=""):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    seo_title = extract(r"\[SEO_TITLE\]\s*:\s*(.+)", raw)
    meta      = extract(r"\[META\]\s*:\s*(.+)", raw)
    slug      = extract(r"\[SLUG\]\s*:\s*(.+)", raw)
    tags_raw  = extract(r"\[TAGS\]\s*:\s*(.+)", raw)
    tags      = [t.strip() for t in tags_raw.split(",")] if tags_raw else ["biohacking", "health", "science"]

    # Extract H1 title
    title = keyword_to_title = ""
    for line in raw.strip().splitlines():
        s = line.strip()
        if s.startswith("# ") and not s.startswith("## "):
            title = s.lstrip("# ").strip()
            break

    # Clean content — remove metadata lines
    content = raw
    for pattern in [r"\[SEO_TITLE\]\s*:.*\n?", r"\[META\]\s*:.*\n?",
                    r"\[SLUG\]\s*:.*\n?", r"\[TAGS\]\s*:.*\n?",
                    r"\[LEAD_MAGNET_\d\]\s*\n?"]:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE)
    content = re.sub(r"^#\s+.+\n?", "", content, count=1, flags=re.MULTILINE)
    content = content.strip()

    if not seo_title:
        seo_title = title or "Biohacking Evidence Review"
    if not meta:
        meta = f"Kai Mercer breaks down the science behind {seo_title.lower()}."
    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "-", (title or seo_title).lower()).strip("-")

    return {
        "title": title or seo_title,
        "seo_title": seo_title,
        "meta": meta,
        "slug": slug,
        "tags": tags,
        "content_markdown": content,
    }


# ---------------------------------------------------------------------------
# SECTION 10 — MARKDOWN TO HTML
# ---------------------------------------------------------------------------
def _inline_md(text):
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def markdown_to_html(md):
    lines = md.split("\n")
    html_parts = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("### "):
            html_parts.append(f"<h3>{_inline_md(stripped[4:].strip())}</h3>")
            i += 1
            continue
        if stripped.startswith("## "):
            html_parts.append(f"<h2>{_inline_md(stripped[3:].strip())}</h2>")
            i += 1
            continue
        if stripped.startswith("# "):
            html_parts.append(f"<h1>{_inline_md(stripped[2:].strip())}</h1>")
            i += 1
            continue

        if re.match(r"^\s*-\s+", line):
            items = []
            while i < n and re.match(r"^\s*-\s+", lines[i]):
                item_text = re.sub(r"^\s*-\s+", "", lines[i])
                items.append(f"<li>{_inline_md(item_text.strip())}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                item_text = re.sub(r"^\s*\d+\.\s+", "", lines[i])
                items.append(f"<li>{_inline_md(item_text.strip())}</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue

        if stripped.startswith(">"):
            bq_lines = []
            while i < n and lines[i].strip().startswith(">"):
                bq_lines.append(lines[i].strip().lstrip(">").strip())
                i += 1
            html_parts.append(f"<blockquote>{_inline_md(' '.join(bq_lines))}</blockquote>")
            continue

        if stripped == "":
            i += 1
            continue

        para_lines = []
        while i < n:
            ln = lines[i]
            s = ln.strip()
            if s == "":
                break
            if (s.startswith("#") or s.startswith(">")
                    or re.match(r"^\s*-\s+", ln)
                    or re.match(r"^\s*\d+\.\s+", ln)):
                break
            para_lines.append(s)
            i += 1
        if para_lines:
            html_parts.append(f"<p>{_inline_md(' '.join(para_lines))}</p>")

    html = "\n".join(html_parts)
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    return html


# ---------------------------------------------------------------------------
# SECTION 11 — PUBLISH TO MEDIUM
# ---------------------------------------------------------------------------
def get_medium_user_id():
    """Fetch Medium user ID from token if not set."""
    if MEDIUM_USER_ID:
        return MEDIUM_USER_ID
    r = requests.get(
        "https://api.medium.com/v1/me",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["data"]["id"]


def publish_medium(article, content_html):
    if not MEDIUM_TOKEN:
        print("[MEDIUM] Token not set — skipping.")
        return None

    try:
        user_id = get_medium_user_id()
        substack_cta = f'\n<p><em>Get weekly evidence breakdowns in <a href="{SUBSTACK_URL}">Biohacking Field Notes</a> — free newsletter by Kai Mercer.</em></p>'
        final_html = content_html + substack_cta

        payload = {
            "title": article["seo_title"],
            "contentFormat": "html",
            "content": final_html,
            "tags": article["tags"][:5],
            "publishStatus": "public",
            "canonicalUrl": f"{SUBSTACK_URL}/p/{article['slug']}" if SUBSTACK_URL else "",
        }

        r = requests.post(
            f"https://api.medium.com/v1/users/{user_id}/posts",
            headers={
                "Authorization": f"Bearer {MEDIUM_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        url = r.json()["data"]["url"]
        print(f"[MEDIUM] Published: {url}")
        return url
    except Exception as e:
        print(f"[MEDIUM] Error: {e}")
        return None


# ---------------------------------------------------------------------------
# SECTION 12 — PUBLISH TO SUBSTACK
# ---------------------------------------------------------------------------
def publish_substack(article, content_html):
    """
    Substack does not have a public publishing API.
    This function uses the private API that the Substack web app uses.
    This may break if Substack changes their internal API.
    """
    if not SUBSTACK_URL or not SUBSTACK_EMAIL or not SUBSTACK_PASSWORD:
        print("[SUBSTACK] Credentials not set — skipping.")
        return None

    try:
        base = SUBSTACK_URL.rstrip("/")

        # Step 1: Login
        session = requests.Session()
        login_r = session.post(
            f"{base}/api/v1/login",
            json={"email": SUBSTACK_EMAIL, "password": SUBSTACK_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if login_r.status_code not in (200, 201):
            print(f"[SUBSTACK] Login failed: {login_r.status_code}")
            return None

        # Step 2: Create draft
        draft_r = session.post(
            f"{base}/api/v1/drafts",
            json={
                "draft_title": article["seo_title"],
                "draft_subtitle": article["meta"],
                "draft_body": json.dumps({"type": "doc", "content": [
                    {"type": "paragraph", "content": [{"type": "html", "text": content_html}]}
                ]}),
                "section_id": None,
                "type": "newsletter",
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if draft_r.status_code not in (200, 201):
            print(f"[SUBSTACK] Draft creation failed: {draft_r.status_code}: {draft_r.text[:200]}")
            return None

        draft_id = draft_r.json().get("id")
        if not draft_id:
            print("[SUBSTACK] No draft ID returned.")
            return None

        # Step 3: Publish
        pub_r = session.post(
            f"{base}/api/v1/posts/{draft_id}/publish",
            json={"send": True, "share_automatically": True},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if pub_r.status_code in (200, 201):
            post_url = f"{base}/p/{article['slug']}"
            print(f"[SUBSTACK] Published: {post_url}")
            return post_url
        else:
            print(f"[SUBSTACK] Publish failed: {pub_r.status_code}: {pub_r.text[:200]}")
            return None

    except Exception as e:
        print(f"[SUBSTACK] Error: {e}")
        return None



# ---------------------------------------------------------------------------
# SECTION 12B — PUBLISH TO VOCAL MEDIA
# ---------------------------------------------------------------------------
def publish_vocal(article, content_html):
    """
    Vocal Media does not have a public API.
    This uses Vocal's internal web API (same as their React app).
    Vocal pays $3.80 per thousand reads (Vocal+: $6.00/thousand).
    Note: Vocal may require manual story approval before it goes live.
    """
    if not VOCAL_EMAIL or not VOCAL_PASSWORD:
        print("[VOCAL] Credentials not set — skipping.")
        return None

    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        # Step 1: Login
        login_r = session.post(
            "https://vocal.media/api/auth/login",
            json={"email": VOCAL_EMAIL, "password": VOCAL_PASSWORD},
            timeout=30,
        )
        if login_r.status_code not in (200, 201):
            print(f"[VOCAL] Login failed: {login_r.status_code}: {login_r.text[:200]}")
            return None

        token = login_r.json().get("token") or login_r.json().get("access_token", "")
        if token:
            session.headers["Authorization"] = f"Bearer {token}"

        # Step 2: Determine best community for biohacking content
        # Vocal communities relevant to biohacking: "longevity", "psyche", "futurism", "lifehack"
        community_slug = "longevity"

        # Step 3: Submit story
        story_r = session.post(
            "https://vocal.media/api/stories",
            json={
                "title": article["seo_title"],
                "subtitle": article["meta"],
                "body": content_html,
                "community": community_slug,
                "tags": article["tags"][:5],
                "status": "pending",  # Vocal requires review before publishing
            },
            timeout=60,
        )

        if story_r.status_code in (200, 201):
            story_data = story_r.json()
            story_id   = story_data.get("id") or story_data.get("story_id", "")
            story_url  = story_data.get("url") or f"https://vocal.media/longevity/{article['slug']}"
            print(f"[VOCAL] Story submitted (pending review): {story_url}")
            return story_url
        else:
            print(f"[VOCAL] Submission failed: {story_r.status_code}: {story_r.text[:200]}")
            return None

    except Exception as e:
        print(f"[VOCAL] Error: {e}")
        return None

# ---------------------------------------------------------------------------
# SECTION 13 — STATE UPDATE
# ---------------------------------------------------------------------------
def update_state(medium_url, substack_url, vocal_url, keyword, title, published_ok):
    """Always log the attempt for debugging, but only consume the daily
    quota (posts_today) when at least one platform actually published.
    This prevents 'ghost posts' from silently eating the day's slot."""
    state = _read_state()
    today = _today_iso()
    state.setdefault("posts_log", []).append({
        "date": today,
        "keyword": keyword,
        "title": title,
        "medium_url": medium_url or "",
        "substack_url": substack_url or "",
        "vocal_url": vocal_url or "",
        "published": published_ok,
    })
    if published_ok:
        state.setdefault("posts_today", []).append(today)
    else:
        # Free the keyword back up so a failed attempt doesn't burn it
        # permanently from the rotation.
        used = _read_used()
        if keyword in used:
            used.remove(keyword)
            with open(USED_KEYWORDS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(used) + ("\n" if used else ""))
    _write_state(state)


# ---------------------------------------------------------------------------
# SECTION 14 — MAIN
# ---------------------------------------------------------------------------
def main():
    load_dotenv()
    print("=" * 55)
    print("Biohacking Content System — Kai Mercer")
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)

    missing = []
    if not GROQ_API_KEY and not GEMINI_API_KEY:
        missing.append("GROQ_API_KEY or GEMINI_API_KEY")
    if not MEDIUM_TOKEN and not SUBSTACK_URL and not VOCAL_EMAIL:
        missing.append("At least one publisher: MEDIUM_TOKEN, SUBSTACK_URL, or VOCAL_EMAIL+VOCAL_PASSWORD")
    if missing:
        print(f"ERROR: Missing secrets: {', '.join(missing)}")
        exit(1)

    key = GROQ_API_KEY or GEMINI_API_KEY
    print(f"[ENV] LLM: {key[:8]}...{key[-4:]}")
    if MEDIUM_TOKEN:
        print(f"[ENV] Medium: configured")
    if SUBSTACK_URL:
        print(f"[ENV] Substack: {SUBSTACK_URL}")
    if VOCAL_EMAIL:
        print(f"[ENV] Vocal Media: {VOCAL_EMAIL}")

    if not should_post_now():
        exit(0)

    # Step 1: Keyword
    print("\n[1/6] Selecting keyword...")
    keyword = get_best_keyword()
    print(f"Keyword: {keyword}")

    sources = pick_sources(keyword)
    print(f"Sources: {[s['name'] for s in sources]}")

    # Step 2: Agent 1 — Scientific Research
    print("\n[2/6] Agent 1: Scientific research pass...")
    research = research_pass(keyword, sources)
    print(f"Research: {len(research.split())} words")

    time.sleep(10)

    # Step 3: Agent 2 — Write Article
    print("\n[3/6] Agent 2: Writing article (Kai Mercer voice)...")
    article_raw = write_article(research, keyword, sources)
    print(f"Draft: {len(article_raw.split())} words")

    time.sleep(10)

    # Step 4: Agent 3 — SEO Review
    print("\n[4/6] Agent 3: SEO review pass...")
    article_final = seo_pass(article_raw, keyword)
    print(f"Final: {len(article_final.split())} words")

    # Step 5: Parse + convert
    print("\n[5/6] Parsing and converting...")
    article = parse_article(article_final)
    print(f"Title: {article['title']}")
    print(f"Slug: {article['slug']}")
    print(f"Tags: {article['tags']}")
    content_html = markdown_to_html(article["content_markdown"])

    # Step 6: Publish
    print("\n[6/6] Publishing to all platforms...")
    medium_url   = publish_medium(article, content_html)
    substack_url = publish_substack(article, content_html)
    vocal_url    = publish_vocal(article, content_html)

    published_ok = any([medium_url, substack_url, vocal_url])
    update_state(medium_url, substack_url, vocal_url, keyword, article["title"], published_ok)

    print("\n" + "=" * 55)
    print("SUCCESS" if published_ok else "FAILED — nothing was actually published")
    print(f"Title    : {article['title']}")
    print(f"Keyword  : {keyword}")
    print(f"Medium   : {medium_url or 'FAILED/skipped'}")
    print(f"Substack : {substack_url or 'FAILED/skipped'}")
    print(f"Vocal    : {vocal_url or 'FAILED/skipped'}")
    print("=" * 55)

    if not published_ok:
        # Non-zero exit makes the GitHub Actions run show as failed/red,
        # instead of silently reporting success while posting nothing.
        exit(1)


if __name__ == "__main__":
    main()
