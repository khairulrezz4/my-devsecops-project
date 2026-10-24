# my-devsecops-project

Security-focused DevSecOps starter project.

Reference guides are in `GUIDES/`:

- `GUIDES/PIPELINE_OVERVIEW.md` explains the complete pipeline flow and
  application setup.
- `GUIDES/DEVSECOPS_WORKFLOW_GUIDE.md` explains repository layout and rollout.
- `GUIDES/AGENT_GUIDE.md` defines safe workflow-editing expectations.
- `GUIDES/SECURITY_GATES_GUIDE.md` documents current and planned security gates.

## CI/CD workflows

`DEVSECOPS_WORKFLOW_MAIN.yml` orchestrates the reusable workflows:

- `reusable-ci.yml` runs build and test commands and optionally uploads an
  artifact.
- `reusable-cd.yml` downloads the artifact and deploys through a protected
  GitHub environment.
- `.github/templates/pipeline_dso.yaml` is a caller template for application
  repositories. Copy it into the application repository's `.github/workflows`
  directory.
- `.github/pipeline/build-list.json` defines the build/test commands and
  artifact paths.
- `.github/pipeline/deployment-targets.json` defines environments, branch
  patterns, and deploy targets.
- `.github/actions/validate-pipeline-config` validates both configuration
  files.
- `.github/actions/initialize-pipeline` performs fail-fast workflow, JSON, and
  immutable-reference checks.
- `.github/actions/node-build` standardizes Node.js installation and builds.
- `.github/actions/python-test` standardizes Python dependency installation and
  tests.

For an application repository, populate `.github/pipeline/build-list.json`.
The reusable CI workflow validates this file and
`.github/pipeline/deployment-targets.json` before running project commands.
When `artifact-path` is provided, CI verifies the tested build output and
uploads it to GitHub artifact storage. Deployment downloads that package,
verifies it is non-empty, and exposes it as `ARTIFACT_PATH` to the deploy
command.
The caller template currently demonstrates a Node application:

```json
{
  "version": 1,
  "buildCommand": "npm run build",
  "testCommand": "npm test",
  "artifacts": [
    {
      "name": "web-dist",
      "path": "dist"
    }
  ]
}
```

Then populate `.github/pipeline/deployment-targets.json` with the provider and
destination.
Keep credentials in GitHub Secrets or OIDC-based environment configuration,
never in these files. The current workflow template does not execute commands
from JSON automatically; commands must be reviewed and passed explicitly as
workflow inputs.

The application template calls the central workflow at:
`khairulrezz4/my-devsecops-project/.github/workflows/DEVSECOPS_WORKFLOW_MAIN.yml`.
Pin `@develop` to a reviewed release commit before production use.

The pipeline runs on all branch pushes so `feature/*` and `hotfix/*` branches
can use CI. Its branch-policy job fails closed if a direct push to `main`,
`develop`, or `release*` is ever received; repository rulesets remain the
primary server-side enforcement.

The Python pipeline POC is in `POC/python`. Its test caller is
`test/workflows/python-poc.yml`; it builds `app.py`, runs the unit test, and
uploads `POC/python/dist` as the `python-poc` artifact. Deployment is disabled
for this POC. The reusable caller template remains generic.
