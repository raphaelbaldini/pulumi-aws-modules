"""DynamoDB table helpers.

For **Aurora PostgreSQL** use :mod:`pulumi_aws_modules.database` (RDS helpers) or
:mod:`pulumi_aws_modules.database.rds` — RDS is a different service than DynamoDB.
"""

from dataclasses import dataclass
from typing import Optional

import pulumi_aws as aws


@dataclass(frozen=True)
class DatabaseResources:
    ingest_metadata_table: aws.dynamodb.Table
    detection_results_table: aws.dynamodb.Table


def create_on_demand_table(
    resource_name: str,
    table_name: str,
    hash_key: str,
    range_key: Optional[str],
    attributes: list[aws.dynamodb.TableAttributeArgs],
    ttl_attribute_name: Optional[str] = None,
    tags: dict[str, str] | None = None,
    *,
    billing_mode: str = "PAY_PER_REQUEST",
    read_capacity: Optional[int] = None,
    write_capacity: Optional[int] = None,
    global_secondary_indexes: Optional[list[aws.dynamodb.TableGlobalSecondaryIndexArgs]] = None,
    deletion_protection_enabled: Optional[bool] = None,
) -> aws.dynamodb.Table:
    """Create a DynamoDB table.

    Defaults to **PAY_PER_REQUEST**. For ``billing_mode="PROVISIONED"``, pass
    ``read_capacity`` and ``write_capacity`` (required for the base table; GSIs
    carry their own capacities on each ``TableGlobalSecondaryIndexArgs``).
    """
    resolved_tags = dict(tags or {})
    resolved_tags.setdefault("Name", table_name)

    if billing_mode == "PROVISIONED":
        if read_capacity is None or write_capacity is None:
            raise ValueError(
                "read_capacity and write_capacity are required when billing_mode is PROVISIONED"
            )
    elif read_capacity is not None or write_capacity is not None:
        raise ValueError("read_capacity and write_capacity are only valid when billing_mode is PROVISIONED")

    ttl = (
        aws.dynamodb.TableTtlArgs(attribute_name=ttl_attribute_name, enabled=True)
        if ttl_attribute_name
        else None
    )

    kwargs: dict = {
        "name": table_name,
        "billing_mode": billing_mode,
        "hash_key": hash_key,
        "attributes": attributes,
        "tags": resolved_tags,
    }
    if range_key is not None:
        kwargs["range_key"] = range_key
    if billing_mode == "PROVISIONED":
        kwargs["read_capacity"] = read_capacity
        kwargs["write_capacity"] = write_capacity
    if global_secondary_indexes:
        kwargs["global_secondary_indexes"] = global_secondary_indexes
    if deletion_protection_enabled is not None:
        kwargs["deletion_protection_enabled"] = deletion_protection_enabled
    if ttl is not None:
        kwargs["ttl"] = ttl

    return aws.dynamodb.Table(resource_name, **kwargs)
