from dataclasses import dataclass

import pulumi
import pulumi_aws as aws

from pulumi_aws_modules.database import DatabaseResources
from pulumi_aws_modules.messaging import MessagingResources
from pulumi_aws_modules.storage import StorageResources


@dataclass(frozen=True)
class IdentityResources:
    worker_role: aws.iam.Role
    worker_instance_profile: aws.iam.InstanceProfile


def create_worker_identity(
    *,
    storage: StorageResources,
    messaging: MessagingResources,
    database: DatabaseResources,
    role_name: str,
    instance_profile_name: str,
    pulumi_resource_prefix: str,
    tags: dict[str, str] | None = None,
) -> IdentityResources:
    """Create an EC2 instance role + profile with SQS, DynamoDB, S3, and SSM read access.

    ``role_name`` / ``instance_profile_name`` are the **AWS** resource names. ``pulumi_resource_prefix``
    must be unique in the stack; it is used to build Pulumi logical resource names
    (``{pulumi_resource_prefix}-role``, etc.).
    """
    assume_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=["sts:AssumeRole"],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["ec2.amazonaws.com"],
                    )
                ],
            )
        ]
    )

    role = aws.iam.Role(
        f"{pulumi_resource_prefix}-role",
        name=role_name,
        assume_role_policy=assume_policy.json,
        tags={**(tags or {}), "Name": role_name},
    )

    policy_doc = pulumi.Output.all(
        messaging.ingest_queue.arn,
        messaging.stage2_queue.arn,
        database.detection_results_table.arn,
        database.ingest_metadata_table.arn,
        storage.raw_video_bucket.arn,
        storage.evidence_bucket.arn,
        storage.reports_bucket.arn,
    ).apply(
        lambda args: pulumi.Output.json_dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "sqs:ReceiveMessage",
                            "sqs:DeleteMessage",
                            "sqs:ChangeMessageVisibility",
                            "sqs:GetQueueAttributes",
                            "sqs:SendMessage",
                        ],
                        "Resource": [args[0], args[1]],
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:GetItem",
                            "dynamodb:Query",
                        ],
                        "Resource": [args[2], args[3]],
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                        "Resource": [
                            args[4],
                            f"{args[4]}/*",
                            args[5],
                            f"{args[5]}/*",
                            args[6],
                            f"{args[6]}/*",
                        ],
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["ssm:GetParameter", "ssm:GetParameters"],
                        "Resource": "*",
                    },
                ],
            }
        )
    )

    aws.iam.RolePolicy(
        f"{pulumi_resource_prefix}-inline-policy",
        role=role.id,
        policy=policy_doc,
    )

    aws.iam.RolePolicyAttachment(
        f"{pulumi_resource_prefix}-ssm-managed-policy",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    )

    instance_profile = aws.iam.InstanceProfile(
        f"{pulumi_resource_prefix}-instance-profile",
        name=instance_profile_name,
        role=role.name,
        tags={**(tags or {}), "Name": instance_profile_name},
    )

    return IdentityResources(
        worker_role=role,
        worker_instance_profile=instance_profile,
    )
