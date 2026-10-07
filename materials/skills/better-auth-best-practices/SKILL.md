---
name: better-auth-best-practices
description: Use when evaluating or using Better Auth for TypeScript authentication, including persistent users and sessions, email/password flows, or plugin integration.
---

# Better Auth

For selection, compare the required account and session behavior with what the library supplies before adding it. For implementation, identify the installed version from the lockfile and follow the matching [official documentation](https://www.better-auth.com/docs/introduction) for adapter, route, schema, and client APIs. Configure a persistent database when accounts or sessions must survive reloads or restarts; check session storage and invalidation behavior against the product requirements.

For email/password authentication, define registration, sign-in, password change and recovery as product flows before selecting library endpoints. Better Auth's email verification and password-reset email mechanisms are optional capabilities, not assumptions about the required interface. Preserve exact error behavior and validate authorization on the server as well as in the UI.

When adding a plugin, check its server and client setup plus schema changes against the installed version. [Official authentication docs](https://www.better-auth.com/docs/authentication/email-password) and [session docs](https://www.better-auth.com/docs/concepts/session-management) are the source for API details; use this skill to choose what to check, then consult those docs for exact calls.
