"""EC2 / Auto Scaling compute primitives."""

from pulumi_aws_modules.compute.ec2 import ComputeResources, create_compute
from pulumi_aws_modules.compute.scaling import create_queue_depth_scaling

__all__ = ["ComputeResources", "create_compute", "create_queue_depth_scaling"]
