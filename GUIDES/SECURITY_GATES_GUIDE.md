# Security gates

The baseline reusable security workflow currently provides:

| Gate | Tool | Evidence |
| --- | --- | --- |
| Secret detection | Gitleaks | Failed job and scanner report |
| Static analysis | CodeQL | Code scanning alert/SARIF plus downloadable HTML/PDF report artifact |
| Workflow and dependency hardening | Planned | Add before production rollout |
| SBOM and artifact provenance | Planned | Add for release workflows |

Recommended next additions are Dependency Review or OSV-Scanner, Trivy for
filesystems and containers, Checkov for infrastructure-as-code, actionlint and
zizmor for workflow review, Dependabot, SBOM generation with Syft, and signed
release attestations.

Security gates should fail closed on new high-severity findings. Tool outages
must be reported as blocked rather than converted into a successful run.
