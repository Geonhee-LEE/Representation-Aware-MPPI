#!/usr/bin/env python3
"""Claude agent for GitHub issue/PR automation.

Adapted from Geonhee-LEE/toy_claude_project/.github/scripts/claude_agent.py
(BSD/MIT-style). Rewritten for this repo:
  - Two actions only: `implement-issue`, `handle-mention`.
  - Diff-output strategy (Claude returns a unified diff; Python applies via
    `git apply`). No tool-use API in this iteration - keeps the surface small.
  - Branch convention `autoresearch/issue-<N>-<slug>` matches the local
    auto-research executor so `gh pr list --search head:autoresearch/` is
    one query for the whole agentic surface.
  - Skips cleanly when ANTHROPIC_API_KEY is missing (defensive: workflow
    already gates this, but importing the module must never sys.exit).
  - Refuses obviously destructive requests (force-push to main, rm -rf,
    delete branch) without calling the API.

Inputs (env, common):
  ANTHROPIC_API_KEY   Anthropic API key (required at runtime).
  GITHUB_TOKEN        Token for `gh` CLI (must be exported as GH_TOKEN too).
  GITHUB_REPOSITORY   owner/repo.

Action `implement-issue` extra env:
  ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY

Action `handle-mention` extra env:
  COMMENT_BODY, COMMENT_ID, ISSUE_NUMBER, IS_PR

Side effects:
  implement-issue -> creates branch, commit, push, opens PR, writes
    `claude_pr_number.txt` (PR number) on success, or `claude_response.md`
    (diagnosis) on failure.
  handle-mention -> posts a Markdown comment on the issue/PR (with a
    `<!-- claude-mention v1 -->` header for de-dup) and adds an `eyes`
    reaction to the original comment.

Exit codes:
  0   success or graceful skip
  1   user-facing failure (diagnosis written to claude_response.md)
  2   misconfiguration (missing required env, bad arguments)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

PRIMARY_MODEL = "claude-opus-4-7"
FALLBACK_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 6144
ANTHROPIC_TIMEOUT_S = 60.0

SYSTEM_PROMPT_BUDGET = 10 * 1024
USER_PROMPT_BUDGET = 30 * 1024
TREE_SAMPLE_LIMIT = 100

MENTION_HEADER = "<!-- claude-mention v1 -->"

# Patterns that block the request before any API call.
DESTRUCTIVE_PATTERNS = [
    re.compile(r"force\s*push.*main",      re.IGNORECASE),
    re.compile(r"force\s*push.*master",    re.IGNORECASE),
    re.compile(r"delete\s+branch",         re.IGNORECASE),
    re.compile(r"rm\s+-rf",                re.IGNORECASE),
    re.compile(r"git\s+reset\s+--hard",    re.IGNORECASE),
    re.compile(r"crontab\s+-r",            re.IGNORECASE),
    re.compile(r"drop\s+(table|database)", re.IGNORECASE),
]


# --------------------------------------------------------------------------- #
# small utilities                                                              #
# --------------------------------------------------------------------------- #


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _require_env(name: str) -> str:
    val = _env(name)
    if not val:
        print(f"ERROR: required env var {name} is empty", file=sys.stderr)
        sys.exit(2)
    return val


def _run(cmd: list[str], *, check: bool = True, capture: bool = True,
         input_text: Optional[str] = None, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
        input=input_text,
        env=env,
    )


def _truncate(text: str, budget_bytes: int, suffix: str = "\n[... truncated ...]\n") -> str:
    raw = text.encode("utf-8", errors="ignore")
    if len(raw) <= budget_bytes:
        return text
    cut = raw[: max(0, budget_bytes - len(suffix.encode("utf-8")))].decode("utf-8", errors="ignore")
    return cut + suffix


def _slug(title: str, words: int = 4) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9 ]+", " ", title).strip().lower()
    parts = [p for p in cleaned.split() if p][:words]
    return "-".join(parts) if parts else "task"


def _is_destructive(body: str) -> Optional[str]:
    for pat in DESTRUCTIVE_PATTERNS:
        if pat.search(body):
            return pat.pattern
    return None


def _project_context() -> str:
    """North-star CLAUDE.md plus a small file-tree sample."""
    parts: list[str] = []
    cm = Path("CLAUDE.md")
    if cm.exists():
        parts.append("## CLAUDE.md (project north star + conventions)\n```\n" + cm.read_text() + "\n```")
    try:
        ls = _run(["git", "ls-files"]).stdout.splitlines()
        parts.append("## Repo layout (first {} tracked files)\n```\n{}\n```".format(
            TREE_SAMPLE_LIMIT, "\n".join(ls[:TREE_SAMPLE_LIMIT])))
    except subprocess.CalledProcessError:
        pass
    joined = "\n\n".join(parts)
    return _truncate(joined, SYSTEM_PROMPT_BUDGET)


# --------------------------------------------------------------------------- #
# Anthropic call (with model fallback + one retry)                             #
# --------------------------------------------------------------------------- #


def call_claude(*, system: str, user: str) -> str:
    import anthropic  # imported here so module import works without the SDK
    client = anthropic.Anthropic(timeout=ANTHROPIC_TIMEOUT_S)
    last_err: Optional[Exception] = None

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        for attempt in range(2):
            try:
                resp = client.messages.create(
                    model=model,
                    max_tokens=MAX_TOKENS,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                text = resp.content[0].text  # type: ignore[attr-defined]
                return f"_(model: `{model}`)_\n\n{text}"
            except Exception as e:  # noqa: BLE001 - retry on any transient failure
                last_err = e
                print(f"WARN: model={model} attempt={attempt} failed: {e}", file=sys.stderr)
                time.sleep(2.0)
    raise RuntimeError(f"all Claude models failed; last error: {last_err}")


# --------------------------------------------------------------------------- #
# Action: implement-issue                                                      #
# --------------------------------------------------------------------------- #

IMPL_SYSTEM_TEMPLATE = """You are an automated coding agent operating on the
Representation-Aware-MPPI repository (ROS2 Jazzy + Gazebo Harmonic, ament_python
package `representation_aware_mppi_bringup`).

# North star (defer ALL ambiguity to this)
모바일 로봇의 주행 MPPI 가 모든 환경에서 물체회피 + 경로추종을 완벽하게 수행한다.

# Project context
{ctx}

# Output contract
Respond in EXACTLY this format:

## Plan
- 1 to 3 bullets describing what you will do.

## Diff
```diff
<unified diff that `git apply -p0` (relative to repo root) can apply cleanly>
```

Rules:
- Use `diff --git a/<path> b/<path>` headers.
- Include `--- a/<path>` and `+++ b/<path>` lines (use `/dev/null` for new/deleted files).
- Only modify files that exist or create new files OUTSIDE `src/` unless the issue
  explicitly requests source changes; doc/script/CI changes are preferred.
- Keep the diff small (<200 lines net) unless the issue explicitly asks for more.
- Do NOT include backticks inside the diff fence.
- Do NOT modify `.github/workflows/ci.yml.disabled` (kept disabled by user).
- No emojis in code; Markdown emojis only when they help readability.
"""


IMPL_USER_TEMPLATE = """# Issue #{n}: {title}

## Body
{body}

Produce the plan + diff per the system contract."""


_DIFF_FENCE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL)


def _extract_diff(response: str) -> Optional[str]:
    m = _DIFF_FENCE.search(response)
    if not m:
        return None
    diff = m.group(1)
    return diff if diff.strip() else None


def _apply_diff(diff: str) -> tuple[bool, str]:
    """Try `git apply` with progressively looser strategies. Returns (ok, log)."""
    diff_path = Path("/tmp/claude_agent_patch.diff")
    diff_path.write_text(diff if diff.endswith("\n") else diff + "\n")
    log_lines: list[str] = []
    for extra in ([], ["--3way"], ["--reject"]):
        cmd = ["git", "apply", "--whitespace=nowarn", *extra, str(diff_path)]
        proc = _run(cmd, check=False)
        log_lines.append(f"$ {' '.join(cmd)}\n{proc.stdout}{proc.stderr}")
        if proc.returncode == 0:
            return True, "\n".join(log_lines)
    return False, "\n".join(log_lines)


def _branch_name(issue_num: int, title: str) -> str:
    return f"autoresearch/issue-{issue_num}-{_slug(title)}"


def _gh_create_pr(*, title: str, body: str, head: str, base: str = "main") -> int:
    body_path = Path("/tmp/claude_agent_pr_body.md")
    body_path.write_text(body)
    proc = _run([
        "gh", "pr", "create",
        "--title", title,
        "--body-file", str(body_path),
        "--head", head,
        "--base", base,
    ])
    # gh prints the PR URL on success; extract the trailing number.
    url = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    m = re.search(r"/pull/(\d+)", url)
    if not m:
        raise RuntimeError(f"could not parse PR number from: {url!r}")
    return int(m.group(1))


def _write_diagnosis(headline: str, detail: str) -> None:
    Path("claude_response.md").write_text(f"**{headline}**\n\n```\n{_truncate(detail, 4000)}\n```\n")


def action_implement_issue() -> int:
    issue_n = int(_require_env("ISSUE_NUMBER"))
    issue_title = _require_env("ISSUE_TITLE")
    issue_body = _env("ISSUE_BODY") or "(no body)"
    repo = _require_env("GITHUB_REPOSITORY")
    _require_env("ANTHROPIC_API_KEY")
    _require_env("GITHUB_TOKEN")

    blocked = _is_destructive(issue_title + "\n" + issue_body)
    if blocked:
        _write_diagnosis(
            "Refused: issue body matched a destructive-operation pattern.",
            f"Blocked pattern: {blocked}\n\nEdit the issue to remove the request and re-label.",
        )
        return 1

    ctx = _project_context()
    system = IMPL_SYSTEM_TEMPLATE.format(ctx=ctx)
    user = _truncate(
        IMPL_USER_TEMPLATE.format(n=issue_n, title=issue_title, body=issue_body),
        USER_PROMPT_BUDGET,
    )

    print(f"calling Claude for issue #{issue_n}: {issue_title!r}")
    try:
        response = call_claude(system=system, user=user)
    except Exception as e:  # noqa: BLE001
        _write_diagnosis("Claude API call failed.", str(e))
        return 1

    diff = _extract_diff(response)
    if not diff:
        _write_diagnosis(
            "Claude response had no ```diff``` fence; nothing to apply.",
            response,
        )
        return 1

    branch = _branch_name(issue_n, issue_title)
    _run(["git", "checkout", "-B", branch])

    ok, log = _apply_diff(diff)
    if not ok:
        _write_diagnosis("`git apply` failed for Claude's diff.", log)
        return 1

    _run(["git", "add", "-A"])
    status = _run(["git", "status", "--porcelain"]).stdout.strip()
    if not status:
        _write_diagnosis("Diff applied but produced no staged changes.", diff)
        return 1

    plan_excerpt = response.split("## Diff")[0].strip()
    commit_body = f"Issue #{issue_n}: {issue_title}\n\n{plan_excerpt}\n"
    msg_path = Path("/tmp/claude_agent_commit_msg.txt")
    msg_path.write_text(f"claude: implement issue #{issue_n}\n\n{commit_body}")
    _run(["git", "commit", "-F", str(msg_path)])

    _run(["git", "push", "-u", "origin", branch, "--force-with-lease"])

    pr_title = f"claude: {issue_title}"
    pr_body = f"{plan_excerpt}\n\nCloses #{issue_n}\n"
    try:
        pr_num = _gh_create_pr(title=pr_title, body=pr_body, head=branch)
    except subprocess.CalledProcessError as e:
        _write_diagnosis("`gh pr create` failed.", f"{e}\n{e.stdout}\n{e.stderr}")
        return 1

    Path("claude_pr_number.txt").write_text(str(pr_num))
    print(f"opened PR #{pr_num} from branch {branch}")
    return 0


# --------------------------------------------------------------------------- #
# Action: handle-mention                                                       #
# --------------------------------------------------------------------------- #

MENTION_SYSTEM_TEMPLATE = """You are responding to a `@claude` mention on a
GitHub issue or PR in the Representation-Aware-MPPI repository.

# North star (anchor every response here)
모바일 로봇의 주행 MPPI 가 모든 환경에서 물체회피 + 경로추종을 완벽하게 수행한다.

# Project context
{ctx}

# Style
- Markdown.
- Senior engineer audience; terse, no fluff.
- Korean is fine when the user wrote Korean; otherwise English.
- No emojis unless the user used them.
- If a concrete change is needed, suggest it as a code block or short bullet list.
  Do NOT attempt to patch the repo from this action - that is the
  `claude-task` workflow's job. Suggest the user open a `claude-task` issue.
"""


MENTION_USER_TEMPLATE = """# Conversation context (issue/PR #{n})
{thread}

# User request (with leading @claude stripped)
{request}

Respond per the system contract."""


def _fetch_thread(repo: str, issue_n: int) -> str:
    """Best-effort issue + recent comments. Falls back to the issue alone."""
    parts: list[str] = []
    try:
        issue = json.loads(_run(["gh", "api", f"repos/{repo}/issues/{issue_n}"]).stdout)
        parts.append(f"## {issue.get('title', '')}\n{issue.get('body') or '(no body)'}")
    except subprocess.CalledProcessError as e:
        parts.append(f"(could not fetch issue: {e})")
    try:
        comments = json.loads(_run(
            ["gh", "api", f"repos/{repo}/issues/{issue_n}/comments?per_page=10"]
        ).stdout)
        for c in comments[-5:]:  # last 5 comments
            user = c.get("user", {}).get("login", "?")
            parts.append(f"### comment by @{user}\n{c.get('body') or ''}")
    except subprocess.CalledProcessError:
        pass
    return _truncate("\n\n".join(parts), USER_PROMPT_BUDGET // 2)


def _react_eyes(repo: str, comment_id: str) -> None:
    try:
        _run([
            "gh", "api", "-X", "POST",
            "-H", "Accept: application/vnd.github+json",
            f"repos/{repo}/issues/comments/{comment_id}/reactions",
            "-f", "content=eyes",
        ], check=False)
    except Exception as e:  # noqa: BLE001 - reactions are best-effort
        print(f"WARN: reaction failed: {e}", file=sys.stderr)


def _post_comment(repo: str, issue_n: int, body: str) -> None:
    full = f"{MENTION_HEADER}\n\n{body}\n"
    out = Path("/tmp/claude_mention_body.md")
    out.write_text(full)
    _run([
        "gh", "issue", "comment", str(issue_n),
        "--repo", repo, "--body-file", str(out),
    ])


def action_handle_mention() -> int:
    repo = _require_env("GITHUB_REPOSITORY")
    issue_n = int(_require_env("ISSUE_NUMBER"))
    comment_id = _require_env("COMMENT_ID")
    raw_body = _env("COMMENT_BODY")
    _require_env("ANTHROPIC_API_KEY")
    _require_env("GITHUB_TOKEN")

    request = re.sub(r"^@claude\b\s*", "", raw_body, flags=re.IGNORECASE).strip()

    _react_eyes(repo, comment_id)

    if not request:
        _post_comment(repo, issue_n, "Hi! Tell me what you'd like me to do (reply with `@claude <request>`).")
        return 0

    blocked = _is_destructive(request)
    if blocked:
        _post_comment(
            repo, issue_n,
            f"Refusing: request matches a destructive-operation guard "
            f"(`{blocked}`). Please rephrase without it.",
        )
        return 0

    ctx = _project_context()
    thread = _fetch_thread(repo, issue_n)
    system = MENTION_SYSTEM_TEMPLATE.format(ctx=ctx)
    user = _truncate(
        MENTION_USER_TEMPLATE.format(n=issue_n, thread=thread, request=request),
        USER_PROMPT_BUDGET,
    )

    print(f"calling Claude for mention on #{issue_n} (is_pr={_env('IS_PR')})")
    try:
        response = call_claude(system=system, user=user)
    except Exception as e:  # noqa: BLE001
        _post_comment(repo, issue_n, f"Sorry, the Claude API call failed:\n\n```\n{e}\n```")
        return 1

    _post_comment(repo, issue_n, response)
    print("posted mention reply")
    return 0


# --------------------------------------------------------------------------- #
# entry point                                                                  #
# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description="Claude GitHub agent")
    parser.add_argument(
        "--action",
        choices=["implement-issue", "handle-mention"],
        required=True,
    )
    args = parser.parse_args()

    if args.action == "implement-issue":
        return action_implement_issue()
    if args.action == "handle-mention":
        return action_handle_mention()
    return 2


if __name__ == "__main__":
    sys.exit(main())
