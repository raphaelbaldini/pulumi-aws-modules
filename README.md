# onii-pulumi-modules

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
pip install "onii-pulumi-modules @ git+file:///Users/rbaldini/Projects/personal/aws/pulumi/onii-pulumi-modules@v0.1.0"
```

## Versioning

Use semantic versioning:

- MAJOR for breaking API changes
- MINOR for backward-compatible features
- PATCH for fixes
