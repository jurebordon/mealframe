# Testing

> Follow these standards for all test code.

## Commands

- Run backend tests: `cd backend && pytest`
- Run frontend lint: `cd frontend && npm run lint`
- Run frontend build: `cd frontend && npm run build`
- Run e2e tests: `cd frontend && npm run test:e2e`

## When to Test

- Run tests before every commit. Do not commit if tests fail.
- Add tests alongside new features and bug fixes.
- Run the full test suite after refactoring, even if changes seem safe.

## Test Quality

- Test behavior, not implementation details. Tests should survive refactoring.
- One assertion concept per test. Test name should describe what is being verified.
- Use descriptive test names: `test_expired_token_returns_401`, not `test_auth_3`.
- Cover edge cases: empty inputs, nulls, boundary values, error paths.
- Never write flaky tests. If a test depends on timing or external state, mock it.
- Keep tests fast. Slow tests get skipped.





