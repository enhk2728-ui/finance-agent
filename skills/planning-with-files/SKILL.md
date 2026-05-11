---
name: planning-with-files
description: External memory for long conversations. Use when starting complex multi-step tasks. Creates plan.md, tasks.md, findings.md to prevent context drift and track progress across long coding sessions.
---

# Planning with Files

## When to Use
Use this skill for ANY task expected to take more than 3 steps or cross multiple files. This prevents context drift in long conversations by maintaining an external plan on disk.

## File Structure

Create three files in the project root (or .claude/plans/ for private plans):

### 1. `plan.md` — The Strategy
- Overall approach and architecture decisions
- Files to create/modify
- Data flow and dependencies
- Constraints and edge cases

### 2. `tasks.md` — The Execution Tracker
- Break plan into small, verifiable steps
- Mark each as `[ ] pending` → `[~] in_progress` → `[x] done`
- One task per logical unit of work
- Update status as you go

### 3. `findings.md` — Discoveries & Decisions
- Surprising discoveries during implementation
- Decisions made and why
- Gotchas for future sessions
- API quirks, workarounds, rejected alternatives

## Workflow

1. **Plan Phase**: Write plan.md first, get user approval
2. **Track Phase**: Copy steps into tasks.md, update live
3. **Document Phase**: Log findings.md as you discover things
4. **Complete Phase**: Verify all tasks [x], ask user to review

## Rules
- NEVER skip the plan file for multi-step work
- Update tasks.md after EVERY step completion
- Log unexpected behavior to findings.md immediately
- Files survive context compression — you can re-read them after a long session
- Delete files when task is fully complete (or ask user to archive)
