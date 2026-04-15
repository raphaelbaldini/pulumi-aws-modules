"""Database primitives (DynamoDB, Aurora PostgreSQL)."""

from pulumi_aws_modules.database.dynamodb import DatabaseResources, create_on_demand_table
from pulumi_aws_modules.database.rds import (
    AuroraPostgresqlClusterResources,
    create_aurora_postgresql_cluster,
)

__all__ = [
    "AuroraPostgresqlClusterResources",
    "DatabaseResources",
    "create_aurora_postgresql_cluster",
    "create_on_demand_table",
]
