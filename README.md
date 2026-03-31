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

Project-specific composition should stay in consuming repos (for example `*_resources.py` files and stack-specific config wiring).

## Install

Using a git tag (example):

```bash
pip install "pulumi-aws-modules @ git+https://github.com/<your-org>/pulumi-aws-modules.git@v0.1.0"
```

For local development:

```bash
pip install "pulumi-aws-modules @ file:///Users/rbaldini/Projects/personal/aws/pulumi/pulumi-aws-modules"
```

## Release and Publish

- Push a tag like `v0.1.0` to trigger `.github/workflows/publish.yml`.
- The workflow builds `sdist` and `wheel`, uploads them to a GitHub Release, and optionally publishes to PyPI when `PYPI_API_TOKEN` is configured.

## Versioning

Use semantic versioning:

- MAJOR for breaking API changes
- MINOR for backward-compatible features
- PATCH for fixes
