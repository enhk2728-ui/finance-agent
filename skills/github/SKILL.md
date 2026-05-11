---
name: github
description: Manage GitHub repositories, PRs, issues, and CI via the gh CLI. Use when the user wants to create/view/merge PRs, manage issues, check CI status, review code, or interact with GitHub in any way from the terminal.
---

# GitHub CLI Skill

## When to Use
Use this skill whenever the user wants to interact with GitHub:
- Create, view, or merge pull requests
- List, create, or comment on issues
- Check CI/CD status, re-run failed jobs
- View repo info, clone, fork
- Review PRs and leave comments
- Search code, issues, or PRs
- Manage releases and tags

## Prerequisites
- `gh` CLI installed and authenticated (`gh auth status`)
- If not authenticated: `gh auth login`

## Common Commands

### Pull Requests
```bash
gh pr list                    # List open PRs
gh pr view [number|url]       # View PR details  
gh pr create --title "..." --body "..."  # Create PR
gh pr merge [number]          # Merge PR
gh pr review [number] --approve|--comment|--request-changes
gh pr diff [number]           # View PR diff
gh pr checks [number]         # View CI checks
```

### Issues
```bash
gh issue list                 # List issues
gh issue view [number]        # View issue
gh issue create --title "..." --body "..."  # Create issue
gh issue comment [number] --body "..."      # Add comment
gh issue close [number]       # Close issue
```

### Repository
```bash
gh repo view [owner/repo]     # View repo info
gh repo clone [owner/repo]    # Clone repo
gh repo fork [owner/repo]     # Fork repo
gh repo create [name]         # Create new repo
```

### CI / Actions
```bash
gh run list                   # List workflow runs
gh run view [id]              # View run details
gh run rerun [id]             # Re-run failed job
gh run watch [id]             # Watch run progress
```

### Search
```bash
gh search repos "topic:finance" --limit 10
gh search issues "bug" --repo owner/repo
gh search prs "fix" --repo owner/repo
```

### Release
```bash
gh release create v1.0.0 --title "Release v1.0.0" --notes "..."
gh release list
```

## Guidelines
- Default to `gh` CLI, NOT raw API calls — simpler, handles auth automatically
- For PR creation: always include a meaningful description, not just title
- After creating a commit/PR, show the user the URL
- Use `gh pr checks` before merging to verify CI is green
- For sensitive operations (force push, delete branch), always confirm with user
