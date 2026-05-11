# Finance Agent Workspace

Financial trading and quantitative analysis workspace. Contains trading system
configurations, price action knowledge base, custom Claude Code skills, and
related automation tools.

## Directory Structure

```
claude/
├── CLAUDE.md           # Workspace entry point
├── settings.json       # Project-level Claude Code config (gitignored)
├── .claude/            # Local Claude Code config
│   └── settings.local.json
├── memory/             # Persistent memory (gitignored — local only)
└── skills/             # Claude Code Skill definitions
    ├── book-to-skill/       # PDF/EPUB → Skill converter
    ├── frontend-design/     # UI design skill
    ├── github/              # GitHub operations
    ├── google-search-console-automation/
    ├── humanize-chinese/    # Chinese text polishing
    ├── llm-wiki/            # LLM Wiki knowledge base
    ├── pdf/                 # PDF processing
    ├── planning-with-files/ # Long-session planning
    ├── skill-creator/       # Skill authoring toolkit
    ├── skill-vetter/        # Security review for skills
    └── xlsx/                # Spreadsheet processing
```

## Skills

Custom Claude Code skills for finance and quantitative analysis workflows.
Each skill under `skills/` contains a `SKILL.md` with usage instructions.

## Price Action Knowledge Base

Al Brooks price action methodology resources are maintained locally in
`memory/price_action/` (not included in this repository).

## Configuration

Model and environment settings are stored in `settings.json` (gitignored).
Copy `settings.json` from your own Claude Code setup as needed.
