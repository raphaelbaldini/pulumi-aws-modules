"""S3-driven events and Lambda wiring."""

from pulumi_aws_modules.events.s3_metadata import (
    EventResources,
    MetadataIngestFanoutConfig,
    MetadataWriterLambdaConfig,
    create_events,
)

__all__ = [
    "EventResources",
    "MetadataIngestFanoutConfig",
    "MetadataWriterLambdaConfig",
    "create_events",
]
