# Security Policy

## Supported Versions

Security fixes target the latest published SVC release. Reports against `main`
are also welcome. Older releases are not maintained separately; users may need
to upgrade to receive a fix.

## Report a Vulnerability

Do not disclose exploitable details in a public issue or pull request. Use
[GitHub private vulnerability reporting](https://github.com/xiaoland/svc/security/advisories/new)
when it is available. If GitHub does not offer the private form, open a public
issue asking for a private contact without including vulnerability details.

Include the affected release or commit, plausible impact, required
preconditions, the trust or authority boundary crossed, and a minimal
reproduction when practical.

## Security Scope

SVC treats a defect as a security vulnerability when it plausibly crosses a
documented trust or authority boundary and causes material execution,
modification, disclosure, or release-integrity impact. Examples include:

- executing data as code or unexpectedly sending local data over a network
- writing to a selected provider source or Consumer-owned file without the
  declared plan and permission
- escaping an intended output boundary or replacing an existing output despite
  an absent-target contract
- compromising the integrity of a distributed package or release artifact

The canonical product boundaries remain in [Product Truth](docs/prd/agent-analysis.md#local-trust-and-exposure-boundary),
[Product TDD](docs/product-tdd/agent-analysis.md#authority-and-topology), and
[Deployment](docs/deployment/agent-analysis.md). In particular,
SVC's Agent-evidence features use a same-user local trust boundary. They do not
promise protection from root, a hostile process under the same account,
adversarial path replacement, or path races. Selected native evidence may
contain all provider content; structural omission is not confidentiality,
privacy, or redaction. The caller owns storage, access, retention, and
disclosure.

A defect that does not cross a security boundary should be reported as an
ordinary public issue. The project does not promise a bug bounty, CVE assignment,
or a fixed response, remediation, or disclosure deadline.
