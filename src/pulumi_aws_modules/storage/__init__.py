"""S3 storage primitives."""

from pulumi_aws_modules.storage.s3 import StorageResources, create_secure_bucket

__all__ = ["StorageResources", "create_secure_bucket"]
