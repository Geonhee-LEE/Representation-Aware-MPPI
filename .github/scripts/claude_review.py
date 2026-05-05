#!/usr/bin/env python3
"""Claude PR review script - posts a single Markdown comment.

Adapted from Geonhee-LEE/toy_claude_project/.github/scripts/claude_agent.py
(BSD/MIT-style). Trimmed to a single action (review-only) and rewritten so
that auth checks are deferred to runtime - importing this module never
requires ANTHROPIC_API_KEY to be set.

Inputs (env):
  ANTHROPIC_API_KEY  Anthropic API key (required at runtime, not import).
  GITHUB_TOKEN       Token for posting the PR comment.
  PR_NUMBER          PR number to review.
  GITHUB_REPOSITORY  owner/repo.

Output:
  Posts a comment on the PR with header `<!-- claude-review v1 -->`.
  Exit 0 on success or graceful skip; exit non-zero only on auth/network
  failure (NOT on "Claude found issues" - that is just feedback).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REVIEW_HEADER = "<!-- claude-review v1 -->"
DIFF_BUDGET_BYTES = 200 * 1024
PRIMARY_MODEL = "claude-opus-4-7"
FALLBACK_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096


def _require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        print(f"ERROR: required env var {name} is empty", file=sys.stderr)
        sys.exit(2)
    return val


def fetch_pr_metadata(repo: str, pr: str) -> dict:
    raw = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{pr}"],
        check=True, capture_output=True, text=True,
    ).stdout
    import json
    return json.loads(raw)


def fetch_pr_diff(repo: str, pr: str) -> str:
    """Fetch unified diff via gh api with diff media type. Truncate to budget."""
    proc = subprocess.run(
        ["gh", "api",
         "-H", "Accept: application/vnd.github.v3.diff",
         f"repos/{repo}/pulls/{pr}"],
        check=True, capture_output=True, text=True,
    )
    diff = proc.stdout
    if len(diff.encode("utf-8")) > DIFF_BUDGET_BYTES:
        cut = diff.encode("utf-8")[:DIFF_BUDGET_BYTES].decode("utf-8", errors="ignore")
        diff = cut + "\n\n[... diff truncated at 200 KB ...]\n"
    return diff


def project_context() -> str:
    parts: list[str] = []
    claude_md = Path("CLAUDE.md")
    if claude_md.exists():
        parts.append("## CLAUDE.md (project context)\n```\n" + claude_md.read_text() + "\n```")
    return "\n\n".join(parts)


def build_prompt(pr_meta: dict, diff: str, ctx: str) -> str:
    title = pr_meta.get("title", "(no title)")
    body = pr_meta.get("body") or "(no PR description)"
    return f"""You are reviewing a pull request on the Representation-Aware-MPPI project.

# PR title
{title}

# PR description (user intent)
{body}

# Project context
{ctx}

# Diff (unified, possibly truncated)
```diff
{diff}
```

Produce a Markdown review with EXACTLY these sections:

## Summary
Two lines max: what this PR does, why.

## Concerns
Bullet list. Cover: correctness, north-star alignment
("모바일 로봇의 주행 MPPI 가 모든 환경에서 물체회피 + 경로추종을 완벽하게"),
simplicity (we deprioritize > 50 net LOC without justification), missing
tests/verification. If none: write "None."

## Suggestions
Concrete, actionable items. If the PR is clean, write exactly:
"looks good - merge".

Be terse. Senior-engineer audience. No emojis."""


def call_claude(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    last_err: Exception | None = None
    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text  # type: ignore[attr-defined]
            return f"_(model: `{model}`)_\n\n{text}"
        except Exception as e:  # noqa: BLE001 - retry on any API failure
            last_err = e
            print(f"WARN: model {model} failed: {e}", file=sys.stderr)
    raise RuntimeError(f"all Claude models failed; last error: {last_err}")


def post_comment(repo: str, pr: str, body: str) -> None:
    full = f"{REVIEW_HEADER}\n\n{body}\n"
    out = Path("/tmp/claude_review_body.md")
    out.write_text(full)
    subprocess.run(
        ["gh", "pr", "comment", pr, "--repo", repo, "--body-file", str(out)],
        check=True,
    )


def main() -> int:
    _require_env("ANTHROPIC_API_KEY")
    _require_env("GITHUB_TOKEN")
    repo = _require_env("GITHUB_REPOSITORY")
    pr = _require_env("PR_NUMBER")

    pr_meta = fetch_pr_metadata(repo, pr)
    diff = fetch_pr_diff(repo, pr)
    if not diff.strip():
        print("empty diff; nothing to review")
        return 0

    prompt = build_prompt(pr_meta, diff, project_context())
    review = call_claude(prompt)
    post_comment(repo, pr, review)
    print("posted review comment")
    return 0


if __name__ == "__main__":
    sys.exit(main())
