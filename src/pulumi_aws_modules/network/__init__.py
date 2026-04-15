"""VPC and networking primitives."""

from pulumi_aws_modules.network.vpc import (
    NetworkResources,
    create_worker_security_group,
    get_default_network,
)

__all__ = ["NetworkResources", "create_worker_security_group", "get_default_network"]
