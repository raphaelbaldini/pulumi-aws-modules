"""CI-related IAM and CodeBuild primitives (GitHub Actions OIDC, worker AMI builds)."""

from __future__ import annotations

from typing import Optional

import json

import pulumi
import pulumi_aws as aws

# GitHub's OIDC thumbprints (rotate per AWS / GitHub docs if validation fails).
_GITHUB_OIDC_THUMBPRINTS = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df240fcd",
]


def create_github_oidc_provider(
    resource_name: str = "github-actions-oidc",
    *,
    tags: Optional[dict[str, str]] = None,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> aws.iam.OpenIdConnectProvider:
    """
    Register ``token.actions.githubusercontent.com`` for GitHub Actions OIDC.

    Only **one** such provider is allowed per AWS account. If it already exists,
    import it instead of creating a duplicate, e.g.::

        pulumi import aws:iam/openIdConnectProvider:OpenIdConnectProvider github-actions-oidc <arn>
    """
    return aws.iam.OpenIdConnectProvider(
        resource_name,
        url="https://token.actions.githubusercontent.com",
        client_id_lists=["sts.amazonaws.com"],
        thumbprint_lists=_GITHUB_OIDC_THUMBPRINTS,
        tags=tags,
        opts=opts,
    )


def oidc_provider_arn_for_account(account_id: pulumi.Input[str]) -> pulumi.Output[str]:
    """Standard ARN for the GitHub OIDC provider (must exist in the account)."""
    return pulumi.Output.format(
        "arn:aws:iam::{}:oidc-provider/token.actions.githubusercontent.com",
        account_id,
    )


def create_github_actions_codebuild_trigger_role(
    resource_name: str,
    role_name: str,
    *,
    oidc_provider_arn: pulumi.Input[str],
    github_repository_subject: str,
    codebuild_project_arn: pulumi.Input[str],
    tags: Optional[dict[str, str]] = None,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> aws.iam.Role:
    """
    Role assumable by GitHub Actions (OIDC) to run ``codebuild:StartBuild``.

    ``github_repository_subject`` is the ``repo:ORG/NAME`` segment used in the OIDC
    ``sub`` claim, e.g. ``repo:acme/onii-video-analytics-worker``.
    """
    assume = pulumi.Output.all(oidc_provider_arn).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Federated": args[0]},
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Condition": {
                            "StringEquals": {
                                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                            },
                            "StringLike": {
                                "token.actions.githubusercontent.com:sub": f"{github_repository_subject}:*",
                            },
                        },
                    }
                ],
            }
        )
    )
    role = aws.iam.Role(
        resource_name,
        name=role_name,
        assume_role_policy=assume,
        tags={**(tags or {}), "Name": role_name},
        opts=opts,
    )
    policy = pulumi.Output.all(codebuild_project_arn).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["codebuild:StartBuild", "codebuild:BatchGetBuilds"],
                        "Resource": args[0],
                    }
                ],
            }
        )
    )
    aws.iam.RolePolicy(
        f"{resource_name}-start-build",
        role=role.id,
        policy=policy,
        opts=pulumi.ResourceOptions(parent=role),
    )
    return role


# Policy allowing Packer (amazon-ebs) + SSM AMI publish from CodeBuild.
_PACKER_CODEBUILD_INLINE_POLICY = json.dumps(
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PackerEC2",
                "Effect": "Allow",
                "Action": [
                    "ec2:AttachVolume",
                    "ec2:AuthorizeSecurityGroupIngress",
                    "ec2:CopyImage",
                    "ec2:CreateImage",
                    "ec2:CreateKeyPair",
                    "ec2:CreateSecurityGroup",
                    "ec2:CreateSnapshot",
                    "ec2:CreateTags",
                    "ec2:CreateVolume",
                    "ec2:DeleteKeyPair",
                    "ec2:DeleteSecurityGroup",
                    "ec2:DeleteSnapshot",
                    "ec2:DeleteVolume",
                    "ec2:DeregisterImage",
                    "ec2:Describe*",
                    "ec2:DetachVolume",
                    "ec2:GetPasswordData",
                    "ec2:ModifyImageAttribute",
                    "ec2:ModifyInstanceAttribute",
                    "ec2:ModifySnapshotAttribute",
                    "ec2:RegisterImage",
                    "ec2:RunInstances",
                    "ec2:StopInstances",
                    "ec2:TerminateInstances",
                ],
                "Resource": "*",
            },
            {
                "Sid": "PackerIAM",
                "Effect": "Allow",
                "Action": [
                    "iam:PassRole",
                    "iam:GetRole",
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:GetRolePolicy",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy",
                    "iam:CreateInstanceProfile",
                    "iam:DeleteInstanceProfile",
                    "iam:AddRoleToInstanceProfile",
                    "iam:RemoveRoleFromInstanceProfile",
                    "iam:TagRole",
                    "iam:TagInstanceProfile",
                    "iam:ListInstanceProfilesForRole",
                    "iam:ListAttachedRolePolicies",
                    "iam:ListRolePolicies",
                ],
                "Resource": "*",
            },
            {
                "Sid": "SSMAmiPointer",
                "Effect": "Allow",
                "Action": ["ssm:PutParameter", "ssm:GetParameter", "ssm:GetParameters"],
                "Resource": "*",
            },
            {
                "Sid": "STS",
                "Effect": "Allow",
                "Action": ["sts:GetCallerIdentity"],
                "Resource": "*",
            },
            {
                "Sid": "CodeConnectionsGitHub",
                "Effect": "Allow",
                "Action": [
                    "codeconnections:GetConnectionToken",
                    "codeconnections:GetConnection",
                    "codeconnections:UseConnection",
                ],
                "Resource": "*",
            },
        ],
    }
)


def create_codebuild_packer_service_role(
    resource_name: str,
    role_name: str,
    *,
    tags: Optional[dict[str, str]] = None,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> aws.iam.Role:
    """IAM role for the CodeBuild project that runs Packer and publishes the AMI id to SSM."""
    assume = aws.iam.get_policy_document_output(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=["sts:AssumeRole"],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["codebuild.amazonaws.com"],
                    )
                ],
            )
        ]
    )
    role = aws.iam.Role(
        resource_name,
        name=role_name,
        assume_role_policy=assume.json,
        tags={**(tags or {}), "Name": role_name},
        opts=opts,
    )
    aws.iam.RolePolicy(
        f"{resource_name}-packer-inline",
        role=role.id,
        policy=_PACKER_CODEBUILD_INLINE_POLICY,
        opts=pulumi.ResourceOptions(parent=role),
    )
    aws.iam.RolePolicyAttachment(
        f"{resource_name}-cb-managed",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
    )
    return role


def create_codebuild_worker_ami_project(
    resource_name: str,
    project_name: str,
    *,
    service_role_arn: pulumi.Input[str],
    github_repo_url: str,
    branch: str,
    buildspec_path: str,
    artifacts_bucket_name: pulumi.Input[str],
    github_code_connection_arn: pulumi.Input[str],
    environment_variables: Optional[list[aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs]] = None,
    compute_type: str = "BUILD_GENERAL1_MEDIUM",
    # Pin or upgrade via https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-available.html
    image: str = "aws/codebuild/amazonlinux2-x86_64-standard:5.0",
    privileged_mode: bool = True,
    tags: Optional[dict[str, str]] = None,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> aws.codebuild.Project:
    """
    CodeBuild project that clones the AMI factory GitHub repo using **AWS CodeConnections**
    (formerly *CodeStar Connections*, rebranded March 2024). Use a connection in *Available*
    state; prefer **GitHub App** connections when offered in the console (see AWS CodeBuild
    user guide: connections / GitHub App).

    ``github_code_connection_arn`` is the connection ARN (``arn:aws:codeconnections:...``).
    """
    env_vars = list(environment_variables or [])
    source = aws.codebuild.ProjectSourceArgs(
        type="GITHUB",
        location=github_repo_url,
        buildspec=buildspec_path,
        git_clone_depth=1,
        report_build_status=False,
        auth=aws.codebuild.ProjectSourceAuthArgs(
            type="OAUTH",
            resource=github_code_connection_arn,
        ),
    )
    return aws.codebuild.Project(
        resource_name,
        name=project_name,
        service_role=service_role_arn,
        artifacts=aws.codebuild.ProjectArtifactsArgs(
            type="S3",
            location=artifacts_bucket_name,
            packaging="NONE",
            path="codebuild",
            name="worker-ami",
        ),
        environment=aws.codebuild.ProjectEnvironmentArgs(
            type="LINUX_CONTAINER",
            compute_type=compute_type,
            image=image,
            privileged_mode=privileged_mode,
            environment_variables=env_vars,
        ),
        source=source,
        tags={**(tags or {}), "Name": project_name},
        opts=opts,
    )
