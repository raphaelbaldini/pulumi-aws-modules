import base64
from dataclasses import dataclass
from typing import Optional

import pulumi
import pulumi_aws as aws

from pulumi_aws_modules.network import NetworkResources


@dataclass(frozen=True)
class ComputeResources:
    worker_asg: aws.autoscaling.Group


def _latest_ami(*, name_pattern: str, owners: list[str]) -> str:
    ami = aws.ec2.get_ami(
        most_recent=True,
        owners=owners,
        filters=[
            {"name": "name", "values": [name_pattern]},
            {"name": "virtualization-type", "values": ["hvm"]},
        ],
    )
    return ami.id


def _resolve_ami_id(
    ami_id: Optional[str],
    ami_ssm_parameter: Optional[str],
    *,
    default_ami_name_pattern: Optional[str],
    default_ami_owners: Optional[list[str]],
) -> pulumi.Input[str]:
    if ami_id:
        return ami_id
    if ami_ssm_parameter:
        return aws.ssm.get_parameter_output(name=ami_ssm_parameter).value
    if default_ami_name_pattern and default_ami_owners:
        return _latest_ami(name_pattern=default_ami_name_pattern, owners=default_ami_owners)
    raise ValueError(
        "Provide worker_ami_id, worker_ami_ssm_parameter, or both default_ami_name_pattern and "
        "default_ami_owners for AMI resolution."
    )


def _create_asg(
    resource_name: str,
    instance_profile_name: pulumi.Input[str],
    network: NetworkResources,
    instance_type: str,
    min_size: int,
    max_size: int,
    ami_image_id: pulumi.Input[str],
    user_data_b64: str,
    launch_template_name_prefix: str,
    asg_name: str,
    instance_name_tag: str,
    asg_name_tag: str,
    spot_max_price: Optional[str] = None,
    tags: dict[str, str] | None = None,
) -> aws.autoscaling.Group:
    resolved_tags = dict(tags or {})
    instance_tags = {**resolved_tags, "Name": instance_name_tag}
    asg_tags = {**resolved_tags, "Name": asg_name_tag}

    launch_template = aws.ec2.LaunchTemplate(
        f"{resource_name}-launch-template",
        name_prefix=launch_template_name_prefix,
        image_id=ami_image_id,
        instance_type=instance_type,
        user_data=user_data_b64,
        iam_instance_profile=aws.ec2.LaunchTemplateIamInstanceProfileArgs(
            name=instance_profile_name
        ),
        instance_market_options=aws.ec2.LaunchTemplateInstanceMarketOptionsArgs(
            market_type="spot",
            spot_options=aws.ec2.LaunchTemplateInstanceMarketOptionsSpotOptionsArgs(
                instance_interruption_behavior="terminate",
                max_price=spot_max_price,
            ),
        ),
        vpc_security_group_ids=[network.worker_security_group_id],
        tag_specifications=[
            aws.ec2.LaunchTemplateTagSpecificationArgs(
                resource_type="instance",
                tags=instance_tags,
            )
        ],
    )

    return aws.autoscaling.Group(
        f"{resource_name}-asg",
        name=asg_name,
        max_size=max_size,
        min_size=min_size,
        desired_capacity=min_size,
        vpc_zone_identifiers=network.subnet_ids,
        launch_template=aws.autoscaling.GroupLaunchTemplateArgs(
            id=launch_template.id,
            version="$Latest",
        ),
        health_check_type="EC2",
        protect_from_scale_in=False,
        tags=[
            aws.autoscaling.GroupTagArgs(key=k, value=v, propagate_at_launch=True)
            for k, v in asg_tags.items()
        ],
    )


def create_compute(
    resource_name: str,
    prefix: str,
    network: NetworkResources,
    instance_profile_name: pulumi.Input[str],
    min_size: int,
    max_size: int,
    instance_types: list[str],
    user_data: str,
    worker_ami_id: Optional[str] = None,
    worker_ami_ssm_parameter: Optional[str] = None,
    default_ami_name_pattern: Optional[str] = None,
    default_ami_owners: Optional[list[str]] = None,
    spot_max_price: Optional[str] = None,
    tags: dict[str, str] | None = None,
) -> ComputeResources:
    """Create an Auto Scaling group; ``user_data`` is a shell script (module base64-encodes it)."""
    launch_template_name_prefix = f"{prefix}-{resource_name}-"
    instance_name_tag = f"{prefix}-{resource_name}"
    user_data_b64 = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")

    worker_asg = _create_asg(
        resource_name=resource_name,
        instance_profile_name=instance_profile_name,
        network=network,
        instance_type=instance_types[0],
        min_size=min_size,
        max_size=max_size,
        ami_image_id=_resolve_ami_id(
            worker_ami_id,
            worker_ami_ssm_parameter,
            default_ami_name_pattern=default_ami_name_pattern,
            default_ami_owners=default_ami_owners,
        ),
        user_data_b64=user_data_b64,
        launch_template_name_prefix=launch_template_name_prefix,
        asg_name=f"{prefix}-{resource_name}-asg",
        instance_name_tag=instance_name_tag,
        asg_name_tag=f"{prefix}-{resource_name}-asg",
        spot_max_price=spot_max_price,
        tags=tags,
    )

    return ComputeResources(worker_asg=worker_asg)
