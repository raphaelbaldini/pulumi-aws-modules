from dataclasses import dataclass

import pulumi_aws as aws


@dataclass(frozen=True)
class NotificationResources:
    sender_identity: aws.ses.EmailIdentity


def create_notifications(
    sender_email: str,
    *,
    identity_resource_name: str,
) -> NotificationResources:
    """Register a SES email identity; ``identity_resource_name`` is the Pulumi logical name."""
    sender_identity = aws.ses.EmailIdentity(
        identity_resource_name,
        email=sender_email,
    )
    return NotificationResources(sender_identity=sender_identity)
