# pulumi-aws-modules

Reusable Pulumi AWS primitive modules for Onii infrastructure projects.

## Scope

This package contains primitive resource builders and typed resource containers. **Stable import paths** for consumers remain `pulumi_aws_modules.<area>` (for example `pulumi_aws_modules.storage`, `pulumi_aws_modules.database`). Implementation is organized under domain subpackages; deep imports such as `pulumi_aws_modules.storage.s3` are optional and not part of the primary API unless you choose to depend on them.

Public areas:

- `storage` — S3 (`create_secure_bucket`, optional `exact_bucket_name` for fixed names / import workflows)
- `messaging` — SQS
- `database` — DynamoDB (`create_on_demand_table`: on-demand by default; optional provisioned + GSIs) and Aurora PostgreSQL (`create_aurora_postgresql_cluster`, also on `database`)
- `network` — VPC / security groups
- `security.iam` — EC2 worker role + instance profile
- `security.ssm` — Parameter Store helpers
- `compute` — EC2 / Auto Scaling
- `compute.scaling` — queue-depth Auto Scaling policies
- `events` — S3 → SQS / Lambda wiring (`create_events` + config dataclasses; **no** stack-specific names or code paths in the module)
- `notifications` — SES (`identity_resource_name` is caller-defined)
- `ssm` — Parameter Store (shim over `security.ssm`)
- `ci` — GitHub OIDC, CodeBuild / Packer helpers

### Layout (under `src/pulumi_aws_modules/`)

| Subpackage        | Implementation modules                          |
|-------------------|-------------------------------------------------|
| `database/`       | `dynamodb.py`, `rds.py`                         |
| `storage/`        | `s3.py`                                         |
| `messaging/`      | `sqs.py`                                        |
| `network/`        | `vpc.py`                                        |
| `notifications/`  | `ses.py`                                        |
| `events/`         | `s3_metadata.py`                                |
| `security/`       | `iam.py`, `ssm.py`                              |
| `compute/`        | `ec2.py`, `scaling.py`                          |
| `ci/`             | `github.py`                                     |

Project-specific composition should stay in consuming repos (for example `*_resources.py` files and stack-specific config wiring).

## Install

Pin to a specific tag in `requirements.txt`:

```
pulumi-aws-modules @ git+https://github.com/raphaelbaldini/pulumi-aws-modules.git@v0.1.0
```

For local development only:

```bash
pip install -e /path/to/pulumi-aws-modules
```

## CI Authentication

Since this repo is private, CI pipelines that install it need a GitHub PAT with `repo` scope. Configure git before `pip install`:

```yaml
- name: Configure git for private repos
  run: git config --global url."https://${{ secrets.MODULES_PAT }}@github.com/".insteadOf "https://github.com/"
```

## Release

Tag a new version and push:

```bash
git tag v0.2.0
git push origin v0.2.0
```

Consumers update their `requirements.txt` tag reference to match.

## Versioning

Use semantic versioning:

- MAJOR for breaking API changes
- MINOR for backward-compatible features
- PATCH for fixes
