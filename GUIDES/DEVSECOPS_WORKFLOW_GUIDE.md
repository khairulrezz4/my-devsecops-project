# DevSecOps workflow guide

## Repository layout

Keep reusable workflows in `.github/workflows/` and application configuration
in `.github/pipeline/`:

```text
.github/
  actions/                 # Repeated local composite actions
  templates/
    pipeline_dso.yaml      # Application caller template
  pipeline/
    build-list.json
    deployment-targets.json
  workflows/                # Active workflows only
```

Application repositories copy `.github/templates/pipeline_dso.yaml` and the
two JSON files.
They call `DEVSECOPS_WORKFLOW_MAIN.yml`, which coordinates branch policy, CI,
security checks, and optional CD.

## Updating the central workflow

1. Make changes on a feature branch.
2. Validate YAML and JSON locally.
3. Review action references and permissions.
4. Merge through pull request.
5. Update application callers from the old immutable commit to the new
   reviewed commit.

Never point production callers at a moving branch. Use a full commit SHA with
an adjacent version comment.

## Trust boundaries

Pull-request source is untrusted. Do not use `pull_request_target` to check out
or execute it. Do not place credentials in JSON configuration. Deployment must
use a protected GitHub environment, scoped credentials, and explicit approval.

The repository ruleset prevents direct pushes to `main`, `develop`, and
`release*`. The workflow branch-policy job is a detection backstop, not a
replacement for the ruleset.
