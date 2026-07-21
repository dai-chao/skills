---
name: github-workflow
description: "Complete GitHub workflow: auth, repos, issues, PRs, code review, CI, releases, and trend analysis."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge, Authentication, Issues, Repositories, Code-Review]
    related_skills: []
---

# GitHub Workflow

Complete guide for the full GitHub development lifecycle: authentication, repository management, issue tracking, pull requests, code review, CI/CD, releases, and open-source trend analysis. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
```

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

---

## Authentication Setup

Two auth paths: `git` (always available) and `gh` CLI (richer API access).

### Detection Flow

```bash
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Decision tree:**
1. If `gh auth status` shows authenticated → use `gh` for everything
2. If `gh` is installed but not authenticated → use "gh auth" method
3. If `gh` is not installed → use "git-only" method (no sudo needed)

### Git-Only: HTTPS with Personal Access Token

**Step 1:** Create a token at https://github.com/settings/tokens with scopes: `repo`, `workflow`, `read:org`.

**Step 2:** Configure git to store the token:

```bash
git config --global credential.helper store
git ls-remote https://github.com/<username>/<any-repo>.git
# Username: <github-username>
# Password: <paste the PAT>
```

**Alternative:** Embed token in the remote URL:
```bash
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**Step 3:** Configure git identity:
```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

### Git-Only: SSH Key Authentication

```bash
# Generate key
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
# Add the public key to https://github.com/settings/keys
ssh -T git@github.com
# Rewrite HTTPS to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### gh CLI Authentication

```bash
# Interactive (desktop)
gh auth login
# Token-based (headless)
echo "<TOKEN>" | gh auth login --with-token
gh auth setup-git
gh auth status
```

### Auth Helper Script

Source the bundled helper to auto-detect auth and set env vars:

```bash
source "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-workflow/scripts/gh-env.sh"
# Sets: GH_AUTH_METHOD, GITHUB_TOKEN, GH_USER, GH_OWNER, GH_REPO, GH_OWNER_REPO
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | Use PAT as password, or switch to SSH |
| `Permission to X denied` | Token lacks `repo` scope — regenerate |
| `Authentication failed` | Cached credentials stale — `git credential reject` then re-auth |
| `ssh: connect to host github.com port 22: refused` | Use `Hostname ssh.github.com` and `Port 443` in `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper` is `store` or `cache` |

---

## Repository Management

### Cloning

```bash
git clone https://github.com/owner/repo-name.git
git clone --depth 1 https://github.com/owner/repo-name.git  # shallow
gh repo clone owner/repo-name  # shorthand
```

### Creating Repositories

**With gh:**
```bash
gh repo create my-project --public --clone
gh repo create my-org/my-project --private --description "A useful tool" --license MIT --clone
```

**With curl:**
```bash
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name": "my-project", "description": "A useful tool", "private": false, "auto_init": true}'
```

### Forking and Sync

```bash
gh repo fork owner/repo-name --clone
# Or curl + git:
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo-name/forks
sleep 3 && git clone https://github.com/$GH_USER/repo-name.git
# Keep fork in sync:
git fetch upstream && git checkout main && git merge upstream/main && git push origin main
# Or: gh repo sync $GH_USER/repo-name
```

### Repo Settings and Branch Protection

```bash
gh repo edit --description "Updated" --visibility public --enable-auto-merge
# Branch protection via API:
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{"required_status_checks": {"strict": true, "contexts": ["ci/test"]}, "required_pull_request_reviews": {"required_approving_review_count": 1}}'
```

### Secrets, Releases, Actions

**Secrets:**
```bash
gh secret set API_KEY --body "value"
gh secret list
```

**Releases:**
```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v2.0.0-rc1 --draft --prerelease
```

**Actions workflows:**
```bash
gh workflow list
gh run list --limit 10
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID>
```

---

## Issue Tracking

### Viewing Issues

**With gh:**
```bash
gh issue list
gh issue list --state open --label "bug"
gh issue list --assignee @me
gh issue view 42
```

**With curl:**
```bash
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&per_page=20" \
  | python3 -c "import sys, json; [print(f\"#{i['number']:5} {i['title']}\") for i in json.load(sys.stdin) if 'pull_request' not in i]"
```

### Creating Issues

**With gh:**
```bash
gh issue create --title "Login redirect ignores ?next=" \
  --body "## Description\nAfter logging in, users always land on /dashboard.\n\n## Steps..." \
  --label "bug,backend" --assignee "username"
```

**With curl:**
```bash
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues \
  -d '{"title": "Login redirect ignores ?next=", "body": "...", "labels": ["bug"], "assignees": ["username"]}'
```

### Managing Issues

| Action | gh | curl |
|--------|-----|------|
| Add labels | `gh issue edit 42 --add-label "priority:high"` | `POST /issues/42/labels` |
| Assign | `gh issue edit 42 --add-assignee @me` | `POST /issues/42/assignees` |
| Comment | `gh issue comment 42 --body "..."` | `POST /issues/42/comments` |
| Close | `gh issue close 42 --reason "not planned"` | `PATCH /issues/42` with `{"state": "closed"}` |
| Reopen | `gh issue reopen 42` | `PATCH /issues/42` with `{"state": "open"}` |
| Link to PR | Add `Closes #42` in PR body | Same |

### Triage Workflow

1. List untriaged: `gh issue list --label "needs-triage" --state open`
2. Read and categorize each issue
3. Apply labels and priority
4. Assign if owner is clear
5. Comment with triage notes

---

## Code Review

### Reviewing Local Changes (Pre-Push)

Pure `git` — works everywhere:

```bash
# Staged changes vs main
git diff --staged
git diff main...HEAD --stat
git diff main...HEAD --name-only
```

**Review checklist:**
- Correctness: does the code do what it claims? Edge cases handled?
- Security: no hardcoded secrets, input validation, no SQL injection/XSS
- Code quality: clear naming, DRY, single responsibility
- Testing: new paths tested, happy path + errors covered
- Performance: no N+1 queries, no blocking in async paths
- Documentation: public APIs documented, non-obvious logic explained

**Present findings as:**
```
## Code Review Summary
### Critical
- file.py:line — description. Suggestion: fix.
### Warnings
- file.py:line — description.
### Suggestions
- file.py:line — description.
### Looks Good
- aspect done well
```

### Reviewing a Pull Request on GitHub

**View PR details:**
```bash
gh pr view 123
gh pr diff 123 --name-only
```

**Check out PR locally:**
```bash
git fetch origin pull/123/head:pr-123 && git checkout pr-123
# Or: gh pr checkout 123
```

**Leave inline comments:**
```bash
gh api repos/$OWNER/$REPO/pulls/123/comments --method POST \
  -f body="Simplify with list comprehension." \
  -f path="src/auth.py" -f commit_id="$HEAD_SHA" -f line=45 -f side="RIGHT"
```

**Submit formal review:**
```bash
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."
```

**With curl — atomic review with multiple inline comments:**
```bash
HEAD_SHA=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/123 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")

curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/123/reviews \
  -d "{\"commit_id\": \"$HEAD_SHA\", \"event\": \"REQUEST_CHANGES\", \"body\": \"Review from Hermes Agent\", \"comments\": [{\"path\": \"src/auth.py\", \"line\": 45, \"body\": \"Use parameterized queries.\"}]}"
```

Event values: `"APPROVE"`, `"REQUEST_CHANGES"`, `"COMMENT"`

### Pre-Commit Verification Pipeline

Automated checks before committing. **Core principle:** no agent verifies its own work.

**Step 1 — Get diff:** `git diff --cached` (or `git diff` if empty)

**Step 2 — Static security scan:**
```bash
git diff --cached | grep "^+" | grep -iE "(api_key|secret|password|token)\s*=\s*['\"][^'\"]{6,}['\"]"
git diff --cached | grep "^+" | grep -E "os\.system\(|subprocess.*shell=True|\beval\(|\bexec\(|pickle\.loads?\("
git diff --cached | grep "^+" | grep -E "execute\(f\"|\.format\(.*SELECT|\.format\(.*INSERT"
```

**Step 3 — Baseline tests and linting:**
```bash
python -m pytest --tb=no -q 2>&1 | tail -5
which ruff && ruff check . 2>&1 | tail -10
which mypy && mypy . --ignore-missing-imports 2>&1 | tail -10
```
Compare against baseline (stash, run, pop) — only NEW failures block.

**Step 4 — Self-review checklist:**
- [ ] No hardcoded secrets
- [ ] Input validation on user data
- [ ] SQL queries parameterized
- [ ] File ops validate paths
- [ ] External calls have error handling
- [ ] No debug prints left behind
- [ ] No commented-out code
- [ ] New code has tests

**Step 5 — Independent reviewer subagent:**
```python
delegate_task(
    goal="""Independent code reviewer. Review the git diff and return ONLY valid JSON.
FAIL-CLOSED: security_concerns non-empty or logic_errors non-empty -> passed=false.
SECURITY: hardcoded secrets, shell injection, SQL injection, path traversal, eval/exec with user input.
LOGIC: wrong conditionals, missing error handling, off-by-one, race conditions.
SUGGESTIONS: missing tests, style, performance, naming (non-blocking).
Return: {"passed": bool, "security_concerns": [], "logic_errors": [], "suggestions": [], "summary": "..."}""",
    context="Independent review. Return only JSON.",
    toolsets=["terminal"]
)
```

**Step 6 — Evaluate:** combine static scan + tests + reviewer.

**Step 7 — Auto-fix (max 2 cycles):**
```python
delegate_task(
    goal="""Fix ONLY the reported issues. Do NOT refactor or add features.""",
    context="Fix only reported issues.",
    toolsets=["terminal", "file"]
)
```

**Step 8 — Commit:** `git add -A && git commit -m "[verified] description"`

---

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

## 6. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## 7. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |

---

## Trend Analysis

Analyze GitHub trending repositories and fast-growing open-source projects.

### Primary Source: GitHub Trending

- URL: https://github.com/trending
- Supports: Language filter, date range (Today / This week / This month)
- Default: ~25 repositories per page

**Extraction script:**
```javascript
// NOTE: must use 'main article' selector — generic 'article' picks up README content
Array.from(document.querySelectorAll('main article')).map(a => {
  const h2 = a.querySelector('h2 a');
  const desc = a.querySelector('p');
  const stars = a.querySelector('a[href*="stargazers"]');
  const lang = a.querySelector('[itemprop="programmingLanguage"]');
  return {
    name: h2?.textContent?.trim().replace(/\s+/g, ' '),
    desc: desc?.textContent?.trim(),
    stars: stars?.textContent?.trim(),
    lang: lang?.textContent?.trim()
  };
}).map(x => JSON.stringify(x)).join('\n')
```

### Analysis Framework

Categorize extracted projects by:

1. **Growth Velocity:** Explosive (>20k stars/month), Fast (10k-20k), Steady (<10k)
2. **Technology Trends:** AI Agent Infrastructure, AI Coding Tools, Video/Content Generation, Privacy/Local-First, Anti-Detection, Infrastructure, Novel Hardware
3. **Language Ecosystem:** Rust, Python, TypeScript, Swift, Go
4. **Developer Type:** Individual vs corporate (Apple, Microsoft, Tencent, NVIDIA)

### Output Format

Present in three tiers:
1. **Top Growth** — fastest rising, with star counts
2. **High-Star Established** — already popular, still trending
3. **Interesting Emerging** — smaller but notable for innovation

Close with **Trend Summary** — 3-5 bullet points on what the data reveals.

### Secondary Source: Hacker News Show

- URL: https://news.ycombinator.com/show
- **Points > 100** = strong interest; **Comments > 50** = active discussion
- Static HTML, no JavaScript needed for basic extraction
- Complements GitHub trending: HN Show = active engagement, GitHub = passive interest

### Pitfalls
- Prefer "This week" or "This month" over "Today" (too noisy)
- Cross-check fork ratios and description quality for inflated stars
- Do NOT rely on web_search — real-time data lags or gets blocked
- Do NOT use `curl` to GitHub API as fallback — often blocked by user consent policy
- Always use `main article` selector, never generic `article`

---

## Codebase Inspection

Analyze repositories for lines of code, language breakdown, and code-vs-comment ratios using `pygount`.

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

**Basic summary:**
```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**IMPORTANT:** Always use `--folders-to-skip` to exclude dependency/build directories, otherwise pygount will crawl them and may hang.

**Project-specific exclusions:**
```bash
# Python: --folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"
# JS/TS:   --folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"
```

**Filter by language:**
```bash
pygount --suffix=py,yaml,yml --format=summary .
```

**Interpreting results:**
- **Language** — detected programming language
- **Files** — number of files
- **Code** — lines of actual code
- **Comment** — lines of comments/documentation
- **Pseudo-languages:** `__empty__`, `__binary__`, `__generated__`, `__duplicate__`, `__unknown__`

**Pitfalls:**
- Markdown shows 0 code lines (classified as comments) — expected
- JSON files show low code counts — use `wc -l` for accurate JSON counts
- Large monorepos: use `--suffix` to target specific languages

---

## Pitfalls

- **Empty diff** — check `git status`, tell user nothing to verify
- **Not a git repo** — skip and tell user
- **Large diff (>15k chars)** — split by file, review each separately
- **delegate_task returns non-JSON** — retry once with stricter prompt, then treat as FAIL
- **Auto-fix introduces new issues** — counts as a new failure, cycle continues
- **GitHub API via curl blocked** — fall back to browser navigation + JavaScript extraction
- **pygount without --folders-to-skip** — will crawl node_modules/venv and hang
- **Markdown = 0 code lines in pygount** — expected behavior, not a bug
- **SSH port 22 blocked** — use `Hostname ssh.github.com` with `Port 443` in `~/.ssh/config`
- **Credentials not persisting** — check `git config --global credential.helper` is `store` or `cache`
