# AI Resume Builder

Paste your resume and a job description, and get back a tailored resume, a skill-match score, and a cover letter — all from the terminal.

## Demo

```text
$ resume-builder --resume me.txt --job jd.txt

Skill Match
  Match score: 57% (8/14 job skills found in your resume)
  ✓ You have: aws, ci/cd, docker, kubernetes, microservices, postgresql, python, rest
  △ Consider adding (mentioned in the job): communication, graphql, kafka,
    leadership, machine learning, terraform

  Tip: add --tailor for an AI-rewritten resume, or --cover-letter.
```

## Features

- **Skill match (offline, no API key)** — scores how many of the job's key skills your resume already mentions, and lists what to add.
- **AI-tailored resume** — Claude rewrites and reorders your resume for the specific role, output as clean Markdown **and** plain text. Truthful — it won't invent experience.
- **Cover-letter generator** — a concise, role-specific cover letter.
- **Highlights matching skills automatically.**
- **Saves** `*_resume.md`, `*_resume.txt`, and `*_cover_letter.txt`.

## Installation

Requires **Python 3.8+**. The skill-match feature is **pure standard library**; `anthropic` is only needed for `--tailor` / `--cover-letter`.

### Linux
```bash
cd linux && ./install.sh
resume-builder --resume ../examples/resume.txt --job ../examples/job-description.txt
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
resume-builder --resume me.txt --job jd.txt
```

### Windows
```powershell
cd windows
python resume.py --resume me.txt --job jd.txt
```

## Usage

```bash
# Skill match only (instant, offline)
resume-builder --resume me.txt --job jd.txt

# AI-tailored resume (Markdown + plain text)
export ANTHROPIC_API_KEY=sk-ant-...
resume-builder --resume me.txt --job jd.txt --tailor -o tailored

# Cover letter
resume-builder --resume me.txt --job jd.txt --cover-letter -o myapp
```

Sample inputs live in `examples/`.

## How it works

1. **Skill match** scans both documents against a library of common skills and reports overlap + gaps — useful even without an API key.
2. **`--tailor`** sends your resume, the job description, and your matched skills to Claude, which returns a rewritten one-page resume.
3. **`--cover-letter`** generates a tailored letter from the same inputs.

## Tech stack

- **Python 3** standard library for skill matching and Markdown→text conversion
- [`anthropic`](https://pypi.org/project/anthropic/) SDK (`claude-opus-4-8`) for tailoring and cover letters

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
