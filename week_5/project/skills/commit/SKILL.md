---
name: commit
description: Stage changes, run tests, and commit with a clean message.
---

# Skill: Conventional Commit Workflow
Goal: Stage changes, run tests, and commit with a clean message.

## Procedure:
1. Run `git status` to see current changes.
2. If tests exist, run `pytest` or `npm test` first.
3. If tests pass, stage files: `git add .`
4. Write a conventional commit message (e.g., "feat: add [feature name]" or "fix: resolve [issue]").
5. Run `git commit -m "[message]"`