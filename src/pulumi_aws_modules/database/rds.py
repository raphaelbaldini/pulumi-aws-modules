"""Aurora PostgreSQL cluster primitives (``aws.rds.Cluster``).

Implementation module for Aurora helpers; symbols are also re-exported from
:mod:`pulumi_aws_modules.database`.
"""

from dataclasses import dataclass
from typing import Optional, Sequence

import pulumi
import pulumi_aws as aws


@dataclass(frozen=True)
class AuroraPostgresqlClusterResources:
    cluster: aws.rds.Cluster


_DEFAULT_IMPORT_IGNORE_CHANGES: tuple[str, ...] = (
    "master_password",
    "master_user_secret",
    "cluster_members",
    "availability_zones",
    "final_snapshot_identifier",
)


def create_aurora_postgresql_cluster(
    resource_name: str,
    *,
    cluster_identifier: str,
    engine_version: str,
    master_username: str,
    db_subnet_group_name: str,
    vpc_security_group_ids: Sequence[str],
    db_cluster_parameter_group_name: Optional[str] = None,
    kms_key_id: Optional[str] = None,
    backup_retention_period: int = 7,
    preferred_backup_window: Optional[str] = None,
    preferred_maintenance_window: Optional[str] = None,
    port: int = 5432,
    allocated_storage: int = 1,
    storage_encrypted: bool = True,
    copy_tags_to_snapshot: bool = True,
    deletion_protection: bool = False,
    enable_http_endpoint: bool = False,
    iam_database_authentication_enabled: bool = False,
    network_type: str = "IPV4",
    auto_minor_version_upgrade: bool = True,
    monitoring_interval: int = 0,
    performance_insights_enabled: bool = False,
    engine_mode: str = "provisioned",
    engine_lifecycle_support: Optional[str] = None,
    database_insights_mode: Optional[str] = None,
    serverlessv2_scaling_configuration: Optional[aws.rds.ClusterServerlessv2ScalingConfigurationArgs] = None,
    tags: Optional[dict[str, str]] = None,
    ignore_changes: Optional[Sequence[str]] = None,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> AuroraPostgresqlClusterResources:
    """
    Create an ``aws.rds.Cluster`` for **Aurora PostgreSQL** (``engine=aurora-postgresql``).

    Default ``ignore_changes`` supports **import-first** stacks (password, members, AZs).

    :param resource_name: Pulumi logical name (often equal to ``cluster_identifier``).
    :param ignore_changes: Extra attribute names to ignore; merged with import-safe defaults.
    """
    resolved_tags = dict(tags or {})
    resolved_tags.setdefault("Name", cluster_identifier)

    merged_ignore = list(_DEFAULT_IMPORT_IGNORE_CHANGES)
    if ignore_changes:
        merged_ignore.extend(str(x) for x in ignore_changes)

    resource_opts = pulumi.ResourceOptions(ignore_changes=merged_ignore)
    final_opts = pulumi.ResourceOptions.merge(opts or pulumi.ResourceOptions(), resource_opts)

    cluster_kwargs: dict = {
        "cluster_identifier": cluster_identifier,
        "engine": "aurora-postgresql",
        "engine_version": engine_version,
        "engine_mode": engine_mode,
        "master_username": master_username,
        "db_subnet_group_name": db_subnet_group_name,
        "vpc_security_group_ids": list(vpc_security_group_ids),
        "backup_retention_period": backup_retention_period,
        "port": port,
        "allocated_storage": allocated_storage,
        "storage_encrypted": storage_encrypted,
        "copy_tags_to_snapshot": copy_tags_to_snapshot,
        "deletion_protection": deletion_protection,
        "enable_http_endpoint": enable_http_endpoint,
        "iam_database_authentication_enabled": iam_database_authentication_enabled,
        "network_type": network_type,
        "auto_minor_version_upgrade": auto_minor_version_upgrade,
        "monitoring_interval": monitoring_interval,
        "performance_insights_enabled": performance_insights_enabled,
        "tags": resolved_tags,
        "opts": final_opts,
    }

    if db_cluster_parameter_group_name:
        cluster_kwargs["db_cluster_parameter_group_name"] = db_cluster_parameter_group_name
    if kms_key_id:
        cluster_kwargs["kms_key_id"] = kms_key_id
    if preferred_backup_window:
        cluster_kwargs["preferred_backup_window"] = preferred_backup_window
    if preferred_maintenance_window:
        cluster_kwargs["preferred_maintenance_window"] = preferred_maintenance_window
    if engine_lifecycle_support:
        cluster_kwargs["engine_lifecycle_support"] = engine_lifecycle_support
    if database_insights_mode:
        cluster_kwargs["database_insights_mode"] = database_insights_mode
    if serverlessv2_scaling_configuration is not None:
        cluster_kwargs["serverlessv2_scaling_configuration"] = serverlessv2_scaling_configuration

    return AuroraPostgresqlClusterResources(
        cluster=aws.rds.Cluster(resource_name, **cluster_kwargs),
    )
