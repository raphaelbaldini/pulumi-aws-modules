# pulumi-aws-modules

Reusable Pulumi AWS primitive modules for Onii infrastructure projects.

## Scope

This package contains primitive resource builders and typed resource containers:

- `storage`
- `messaging`
- `database`
- `network`
- `iam`
- `compute`
- `scaling`
- `events`
- `notifications`
- `ssm` (Parameter Store: `create_string_parameter`, `create_secure_string_parameter`, `get_parameter_value`)

Project-specific composition should stay in consuming repos (for example `*_resources.py` files and stack-specific config wiring).

## Install

Pin to a specific tag in `requirements.txt`:

```
pulumi-aws-modules @ git+https://github.com/raphaelbaldini/pulumi-aws-modules.git@v0.1.0
```

For local development only:

```bash
pip install "pulumi-aws-modules @ file:///Users/rbaldini/Projects/personal/aws/pulumi/pulumi-aws-modules"
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
