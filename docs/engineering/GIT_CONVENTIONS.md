# Git Conventions

## Purpose

This document defines the Git workflow and commit conventions for the YT Signal Scout project to ensure a clean, understandable, and maintainable version history.

---

## Branch Naming

Use descriptive branch names following the format below.

```
feature/<feature-name>
bugfix/<issue-name>
hotfix/<issue-name>
refactor/<component>
docs/<document>
chore/<task>
```

### Examples

```
feature/youtube-scanner
feature/google-auth
bugfix/oauth-callback
refactor/scoring-engine
docs/prd-update
chore/dependency-upgrade
```

---

## Commit Message Format

Use the following format for every commit.

```
<type>: <short description>
```

### Examples

```
feat: add FastAPI application bootstrap
fix: resolve OAuth callback issue
refactor: extract scoring service
docs: update PRD search workflow
test: add unit tests for channel repository
chore: update project dependencies
```

---

## Allowed Commit Types

| Type | Purpose |
|------|---------|
| feat | New feature |
| fix | Bug fix |
| refactor | Improve code without changing behavior |
| docs | Documentation updates |
| test | Add or modify tests |
| chore | Maintenance tasks |
| perf | Performance improvements |
| ci | CI/CD configuration |
| build | Build or dependency changes |

---

## General Guidelines

- Keep commits focused on a single logical change.
- Avoid mixing unrelated changes in one commit.
- Write commit messages in the imperative mood.
- Commit frequently during development.
- Ensure the project builds successfully before committing.
- Never commit secrets, credentials, or API keys.

---

## Pull Request Guidelines

- Keep pull requests small and focused.
- Reference the related feature or issue.
- Ensure all tests pass before merging.
- Update documentation when functionality changes.
- Request review before merging into the main branch.

---

## Version Control Principles

- `main` should always remain deployable.
- Every commit should leave the repository in a working state.
- Documentation and code should evolve together.
- Prefer many small commits over one large commit.