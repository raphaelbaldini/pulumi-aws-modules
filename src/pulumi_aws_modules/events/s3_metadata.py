import json
from dataclasses import dataclass, field
from typing import Any, Mapping

import pulumi
import pulumi_aws as aws

from pulumi_aws_modules.database import DatabaseResources
from pulumi_aws_modules.messaging import MessagingResources
from pulumi_aws_modules.storage import StorageResources


@dataclass(frozen=True)
class EventResources:
    metadata_lambda: aws.lambda_.Function


@dataclass(frozen=True)
class MetadataIngestFanoutConfig:
    """Pulumi logical resource names and IAM sid for raw bucket → ingest queue + Lambda notifications."""

    ingest_queue_policy_pulumi_name: str
    source_bucket_to_queue_policy_sid: str
    lambda_invoke_permission_logical_name: str
    bucket_notification_logical_name: str


@dataclass(frozen=True)
class MetadataWriterLambdaConfig:
    """Lambda + IAM role wiring; all names and artifact paths come from the caller."""

    lambda_role_logical_name: str
    iam_role_name: str
    basic_execution_attachment_logical_name: str
    inline_policy_logical_name: str
    function_logical_name: str
    function_name: str
    runtime: str
    handler: str
    code: pulumi.Input[Any]
    timeout_seconds: int
    environment: Mapping[str, pulumi.Input[str]] = field(default_factory=dict)


def _allow_s3_to_send_to_queue(
    queue_policy_pulumi_name: str, queue: aws.sqs.Queue, bucket_arn: pulumi.Input[str], sid: str
) -> None:
    policy = pulumi.Output.all(queue.arn, bucket_arn).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": sid,
                        "Effect": "Allow",
                        "Principal": {"Service": "s3.amazonaws.com"},
                        "Action": "sqs:SendMessage",
                        "Resource": args[0],
                        "Condition": {"ArnEquals": {"aws:SourceArn": args[1]}},
                    }
                ],
            }
        )
    )
    aws.sqs.QueuePolicy(queue_policy_pulumi_name, queue_url=queue.id, policy=policy)


def create_events(
    storage: StorageResources,
    messaging: MessagingResources,
    database: DatabaseResources,
    *,
    fanout: MetadataIngestFanoutConfig,
    metadata_lambda: MetadataWriterLambdaConfig,
) -> EventResources:
    """Wire S3 object-created events to SQS and a metadata Lambda; caller supplies all names and code."""
    _allow_s3_to_send_to_queue(
        fanout.ingest_queue_policy_pulumi_name,
        queue=messaging.ingest_queue,
        bucket_arn=storage.raw_video_bucket.arn,
        sid=fanout.source_bucket_to_queue_policy_sid,
    )

    lambda_assume_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=["sts:AssumeRole"],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service", identifiers=["lambda.amazonaws.com"]
                    )
                ],
            )
        ]
    )

    metadata_lambda_role = aws.iam.Role(
        metadata_lambda.lambda_role_logical_name,
        name=metadata_lambda.iam_role_name,
        assume_role_policy=lambda_assume_policy.json,
    )

    aws.iam.RolePolicyAttachment(
        metadata_lambda.basic_execution_attachment_logical_name,
        role=metadata_lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    metadata_policy = pulumi.Output.all(database.ingest_metadata_table.arn).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["dynamodb:PutItem", "dynamodb:UpdateItem"],
                        "Resource": [args[0]],
                    }
                ],
            }
        )
    )

    aws.iam.RolePolicy(
        metadata_lambda.inline_policy_logical_name,
        role=metadata_lambda_role.id,
        policy=metadata_policy,
    )

    fn = aws.lambda_.Function(
        metadata_lambda.function_logical_name,
        name=metadata_lambda.function_name,
        runtime=metadata_lambda.runtime,
        role=metadata_lambda_role.arn,
        handler=metadata_lambda.handler,
        timeout=metadata_lambda.timeout_seconds,
        code=metadata_lambda.code,
        environment=aws.lambda_.FunctionEnvironmentArgs(
            variables=dict(metadata_lambda.environment),
        ),
    )

    invoke_permission = aws.lambda_.Permission(
        fanout.lambda_invoke_permission_logical_name,
        action="lambda:InvokeFunction",
        function=fn.name,
        principal="s3.amazonaws.com",
        source_arn=storage.raw_video_bucket.arn,
    )

    aws.s3.BucketNotification(
        fanout.bucket_notification_logical_name,
        bucket=storage.raw_video_bucket.id,
        queues=[
            aws.s3.BucketNotificationQueueArgs(
                queue_arn=messaging.ingest_queue.arn,
                events=["s3:ObjectCreated:*"],
            )
        ],
        lambda_functions=[
            aws.s3.BucketNotificationLambdaFunctionArgs(
                lambda_function_arn=fn.arn,
                events=["s3:ObjectCreated:*"],
            )
        ],
        opts=pulumi.ResourceOptions(depends_on=[invoke_permission]),
    )

    return EventResources(metadata_lambda=fn)
