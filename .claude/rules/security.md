# Security

> Follow these rules to prevent security vulnerabilities.

## Secrets and Credentials

- Never commit secrets, API keys, tokens, or passwords to the repository.
- Never hardcode credentials. Use environment variables or a secrets manager.
- Do not read, output, or log the contents of `.env`, `*.pem`, `*.key`, `credentials.*`, or `*secret*` files.
- If a secret is accidentally committed, alert the user immediately. Do not just delete it.
- Use `.gitignore` to exclude sensitive files. Verify before every commit.

## Input and Data

- Validate and sanitize all external input. Never trust user-provided data.
- Use parameterized queries for database operations. Never construct SQL with string concatenation.
- Escape output to prevent injection attacks (XSS, SQL injection, command injection).
- Apply the principle of least privilege for file access, API permissions, and database roles.

## Dependencies

- Keep dependencies updated. Known vulnerabilities in old versions are exploitable.
- Never disable SSL/TLS verification, even in development.
- Review new dependencies before adding them. Prefer well-maintained, widely-used libraries.





## General Awareness

- Follow OWASP Top 10 guidelines for web applications.
- Log security-relevant events (auth failures, permission denials) but never log secrets.
- Use HTTPS for all external communication.
