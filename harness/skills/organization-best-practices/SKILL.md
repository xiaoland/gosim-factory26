---
name: organization-best-practices
description: Use when evaluating or using Better Auth's organization plugin for organizations, members, teams, invitations, or role and permission integration.
---

# Better Auth organization plugin

First compare the product's organization behavior with the [organization plugin](https://www.better-auth.com/docs/plugins/organization). If selected, install its server and client plugins and required schema for the project's Better Auth version. The plugin can manage organization members, teams, invitations, and roles; it does not define the application's repository, issue, or review permissions.

Write down the product's allowed operations and effective permission rules before mapping them to plugin roles. Check how active organization, direct membership, team membership, invitations, and removal affect each operation. A plugin default role or inherited team relationship is only valid when it matches the product requirement. Recheck server permission enforcement and persisted state after a membership or role change.

Consult the [official plugin documentation](https://www.better-auth.com/docs/plugins/organization) for version-specific API calls and access-control setup. Use `better-auth-best-practices` for base authentication and session questions.
