from dataclasses import dataclass

import pulumi
import pulumi_aws as aws


@dataclass(frozen=True)
class NetworkResources:
    vpc_id: pulumi.Output[str]
    subnet_ids: pulumi.Output[list[str]]
    worker_security_group_id: pulumi.Output[str]


def get_default_network() -> tuple[str, list[str]]:
    default_vpc = aws.ec2.get_vpc(default=True)
    default_subnets = aws.ec2.get_subnets(filters=[{"name": "vpc-id", "values": [default_vpc.id]}])
    return default_vpc.id, default_subnets.ids


def create_worker_security_group(
    *,
    vpc_id: str,
    security_group_name: str,
    security_group_description: str,
    security_group_resource_name: str,
    tags: dict[str, str] | None = None,
) -> aws.ec2.SecurityGroup:
    """Create a security group; caller supplies AWS name, description, and Pulumi logical name."""
    resolved_tags = dict(tags or {})
    resolved_tags.setdefault("Name", security_group_name)

    return aws.ec2.SecurityGroup(
        security_group_resource_name,
        name=security_group_name,
        description=security_group_description,
        vpc_id=vpc_id,
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
                ipv6_cidr_blocks=["::/0"],
            )
        ],
        tags=resolved_tags,
    )
