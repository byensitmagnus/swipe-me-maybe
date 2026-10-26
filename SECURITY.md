# Security and privacy

This is an experimental project without a supported production release.
Use the latest source when investigating a problem.

For a vulnerability, use the repository's **Security → Report a vulnerability**
flow. Do not include working credentials, certificates, real profile data,
full device logs or accessibility dumps. A synthetic reproduction is preferred.
If private reporting is unavailable, open a content-free issue asking a
maintainer to arrange a private report; do not disclose the exploit there.

The dashboard and Appium must remain bound to loopback. Do not expose them
through a public tunnel, disable Host/Origin/token checks or publish `.local/`.
Signing keys and Apple credentials belong in local signing tools, never this app.

The project does not provide an account-ban avoidance mechanism. For ordinary
setup problems, use the bug template rather than the security-report flow.
