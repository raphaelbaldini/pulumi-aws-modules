"""SQS messaging primitives."""

from pulumi_aws_modules.messaging.sqs import MessagingResources, create_queue_with_dlq

__all__ = ["MessagingResources", "create_queue_with_dlq"]
