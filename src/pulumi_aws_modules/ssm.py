"""AWS Systems Manager Parameter Store primitives."""

from __future__ import annotations

from typing import Optional

import pulumi
import pulumi_aws as aws


def create_string_parameter(
    resource_name: str,
    parameter_name: str,
    value: pulumi.Input[str],
    *,
    description: Optional[str] = None,
    tier: Optional[str] = None,
    tags: Optional[dict[str, str]] = None,
    overwrite: bool = True,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> aws.ssm.Parameter:
    """Create or update a plain String SSM parameter."""
    args: dict[str, object] = {
        "name": parameter_name,
        "type": aws.ssm.ParameterType.STRING,
        "value": value,
        "overwrite": overwrite,
    }
    if description is not None:
        args["description"] = description
    if tier is not None:
        args["tier"] = tier
    if tags is not None:
        args["tags"] = tags
    return aws.ssm.Parameter(resource_name, opts=opts, **args)


def create_secure_string_parameter(
    resource_name: str,
    parameter_name: str,
    value: pulumi.Input[str],
    *,
    description: Optional[str] = None,
    tier: Optional[str] = None,
    kms_key_id: Optional[pulumi.Input[str]] = None,
    tags: Optional[dict[str, str]] = None,
    overwrite: bool = True,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> aws.ssm.Parameter:
    """Create or update a SecureString SSM parameter."""
    args: dict[str, object] = {
        "name": parameter_name,
        "type": aws.ssm.ParameterType.SECURE_STRING,
        "value": value,
        "overwrite": overwrite,
    }
    if description is not None:
        args["description"] = description
    if tier is not None:
        args["tier"] = tier
    if kms_key_id is not None:
        args["kms_key_id"] = kms_key_id
    if tags is not None:
        args["tags"] = tags
    return aws.ssm.Parameter(resource_name, opts=opts, **args)


def get_parameter_value(name: str, *, with_decryption: bool = True) -> pulumi.Output[str]:
    """Read an existing parameter at preview/update time (data source)."""
    return aws.ssm.get_parameter_output(name=name, with_decryption=with_decryption).value
