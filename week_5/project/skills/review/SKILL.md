---
name: review
description: Review code quality, identify bugs, and check for maintainability issues.
---

# Skill: Code Quality Review
Goal: Identify bugs and maintainability issues.

## Checklist:
- [ ] Are there hardcoded secrets or API keys? (Flag immediately!)
- [ ] Is error handling present for file I/O operations?
- [ ] Does the code follow the existing project style?
- [ ] Are docstrings or comments included for complex logic?
- [ ] Check for "TODO" comments—can the agent resolve them now?

## Procedure:
1. Read the file provided for review.
2. Compare against the checklist above.
3. Provide a summary of issues found.
4. If critical issues are found, suggest a refactor plan.