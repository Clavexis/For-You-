#!/usr/bin/env python3
"""
AI Resume Builder — tailor your resume to a job description.

  - Input: your base resume + a job description.
  - Skill match: finds which of the job's key skills your resume already
    mentions (works offline, no API key needed).
  - AI tailoring: Claude rewrites and reorders your resume for the role,
    output as Markdown and plain text.
  - Cover-letter generator.

Usage:
  resume.py --resume me.txt --job jd.txt                 # skill match (offline)
  resume.py --resume me.txt --job jd.txt --tailor        # AI-tailored resume
  resume.py --resume me.txt --job jd.txt --cover-letter  # cover letter
  resume.py --resume me.txt --job jd.txt --tailor -o out

Built by clavexis — github.com/clavexis
"""

import argparse
import os
import re
import sys
from pathlib import Path

DEFAULT_MODEL = "claude-opus-4-8"


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"; CYAN = "\033[36m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "GREEN", "YELLOW", "RED", "CYAN"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


# A library of common tech/role skills to look for in a job description.
SKILL_LIBRARY = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "sql", "nosql", "postgresql", "mysql",
    "mongodb", "redis", "react", "angular", "vue", "node.js", "django", "flask",
    "fastapi", "spring", "express", "docker", "kubernetes", "aws", "azure", "gcp",
    "terraform", "ansible", "ci/cd", "jenkins", "git", "linux", "bash",
    "machine learning", "deep learning", "tensorflow", "pytorch", "pandas",
    "numpy", "data analysis", "rest", "graphql", "microservices", "agile",
    "scrum", "kafka", "rabbitmq", "elasticsearch", "html", "css", "tailwind",
    "figma", "ux", "ui", "testing", "pytest", "jest", "security", "devops",
    "leadership", "communication", "project management", "api", "cloud",
]


def find_skills(text: str) -> set:
    """Return the library skills mentioned in the text (whole-word, case-insensitive)."""
    low = text.lower()
    found = set()
    for skill in SKILL_LIBRARY:
        # Escape regex specials (e.g. c++, node.js) and match as a token.
        pat = re.escape(skill)
        if re.search(rf"(?<![a-z0-9]){pat}(?![a-z0-9])", low):
            found.add(skill)
    return found


def skill_match_report(resume: str, job: str) -> dict:
    job_skills = find_skills(job)
    resume_skills = find_skills(resume)
    matched = sorted(job_skills & resume_skills)
    missing = sorted(job_skills - resume_skills)
    pct = round(100 * len(matched) / len(job_skills)) if job_skills else 0
    return {
        "job_skills": sorted(job_skills),
        "matched": matched,
        "missing": missing,
        "match_pct": pct,
    }


def print_skill_match(r: dict):
    print(f"\n{C.CYAN}{C.BOLD}Skill Match{C.RESET}")
    color = C.GREEN if r["match_pct"] >= 70 else C.YELLOW if r["match_pct"] >= 40 else C.RED
    print(f"  Match score: {color}{r['match_pct']}%{C.RESET} "
          f"({len(r['matched'])}/{len(r['job_skills'])} job skills found in your resume)")
    if r["matched"]:
        print(f"  {C.GREEN}✓ You have:{C.RESET} {', '.join(r['matched'])}")
    if r["missing"]:
        print(f"  {C.YELLOW}△ Consider adding (mentioned in the job):{C.RESET} "
              f"{', '.join(r['missing'])}")
    print()


# ---------------------------------------------------------------------------
# AI features
# ---------------------------------------------------------------------------
def get_client():
    try:
        import anthropic
    except ImportError:
        sys.stderr.write("AI features need 'anthropic'.  pip install anthropic\n")
        return None
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.stderr.write("Set ANTHROPIC_API_KEY to use AI features.\n")
        return None
    return anthropic.Anthropic(api_key=key)


def ai_call(client, system, user, max_tokens=2500):
    chunks = []
    with client.messages.stream(model=DEFAULT_MODEL, max_tokens=max_tokens,
                                system=system, messages=[{"role": "user", "content": user}]) as stream:
        for text in stream.text_stream:
            chunks.append(text)
            print(text, end="", flush=True)
    print()
    return "".join(chunks)


def tailor_resume(client, resume, job, matched):
    system = (
        "You are an expert resume writer and career coach. Rewrite the candidate's "
        "resume to be tailored to the target job description. Keep it truthful — "
        "do not invent experience. Reorder and reword to surface relevant skills, "
        "use strong action verbs and quantified achievements where present, and "
        "keep it concise (one page). Output clean Markdown."
    )
    user = (f"# Target job description\n{job}\n\n"
            f"# My current resume\n{resume}\n\n"
            f"# Skills I already have that the job wants\n{', '.join(matched)}\n\n"
            "Rewrite my resume tailored to this job.")
    return ai_call(client, system, user)


def cover_letter(client, resume, job):
    system = (
        "You are a professional cover-letter writer. Write a concise, compelling "
        "cover letter (3-4 short paragraphs) connecting the candidate's background "
        "to the role. Be specific, warm, and professional. Plain prose, no clichés."
    )
    user = f"# Job description\n{job}\n\n# Candidate resume\n{resume}\n\nWrite the cover letter."
    return ai_call(client, system, user, max_tokens=1200)


def markdown_to_plain(md: str) -> str:
    """Lightweight Markdown -> plain text for the .txt output."""
    text = re.sub(r"^#{1,6}\s*", "", md, flags=re.M)     # headings
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)          # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)              # italics
    text = re.sub(r"^\s*[-*]\s+", "  - ", text, flags=re.M)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Tailor your resume to a job description.")
    ap.add_argument("--resume", required=True, help="Path to your base resume (text).")
    ap.add_argument("--job", required=True, help="Path to the job description (text).")
    ap.add_argument("--tailor", action="store_true", help="AI-tailor the resume.")
    ap.add_argument("--cover-letter", action="store_true", help="Generate a cover letter.")
    ap.add_argument("-o", "--out", help="Output basename (writes .md and .txt).")
    args = ap.parse_args()

    try:
        resume = Path(args.resume).read_text()
        job = Path(args.job).read_text()
    except OSError as exc:
        sys.stderr.write(f"{C.RED}Could not read input: {exc}{C.RESET}\n")
        return 1

    # Skill match always runs (offline, no key).
    match = skill_match_report(resume, job)
    print_skill_match(match)

    if not args.tailor and not args.cover_letter:
        print(f"{C.DIM}Tip: add --tailor for an AI-rewritten resume, "
              f"or --cover-letter to generate a cover letter.{C.RESET}")
        return 0

    client = get_client()
    if not client:
        return 1

    outputs = {}
    if args.tailor:
        print(f"\n{C.CYAN}{C.BOLD}Tailored Resume{C.RESET}\n")
        outputs["resume"] = tailor_resume(client, resume, job, match["matched"])
    if args.cover_letter:
        print(f"\n{C.CYAN}{C.BOLD}Cover Letter{C.RESET}\n")
        outputs["cover_letter"] = cover_letter(client, resume, job)

    if args.out:
        base = args.out
        if "resume" in outputs:
            Path(f"{base}_resume.md").write_text(outputs["resume"])
            Path(f"{base}_resume.txt").write_text(markdown_to_plain(outputs["resume"]))
            print(f"\n{C.GREEN}Saved {base}_resume.md and {base}_resume.txt{C.RESET}")
        if "cover_letter" in outputs:
            Path(f"{base}_cover_letter.txt").write_text(outputs["cover_letter"])
            print(f"{C.GREEN}Saved {base}_cover_letter.txt{C.RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
