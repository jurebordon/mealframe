# Git Workflow

> Follow these conventions for all git operations.

## Branches

- Create branches from `main` using the `feat/description` pattern.
- Examples: `feat/add-search`, `fix/null-pointer`, `refactor/auth-module`.
- Keep branches short-lived. One feature or fix per branch.

## Commits

- Format: `type: concise description` (lowercase, imperative mood, no period).
- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
- Make atomic commits. Each commit should compile and pass tests.
- Add co-author line for AI-assisted work:
  ```
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

## Ticket References

- Include ticket reference in commit body: ``.
- Reference tickets in PR/MR descriptions.

## Pre-Commit Checks

Run these before every commit:

- Tests: `# Detected by /init-specflow`
- Lint: `# Detected by /init-specflow`
- Build: `# Detected by /init-specflow`

Fix failures before committing. Do not commit broken code.

## Solo Workflow

- Work on feature branches, merge to `main` when tests pass.
- Push frequently to keep the remote in sync.
- Delete branches after merging.
- No PR required for small fixes directly on `main`.


