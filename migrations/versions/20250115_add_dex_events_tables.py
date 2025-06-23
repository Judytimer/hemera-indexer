"""add_dex_events_tables

Revision ID: dex_events_001
Revises: f846e3abeb18
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "dex_events_001"
down_revision: Union[str, None] = "f846e3abeb18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create DEX swap events table
    op.create_table(
        "af_dex_swap_events",
        sa.Column("transaction_hash", postgresql.BYTEA(), nullable=False),
        sa.Column("log_index", sa.INTEGER(), nullable=False),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("sender", postgresql.BYTEA(), nullable=False),
        sa.Column("to_address", postgresql.BYTEA(), nullable=True),
        # V2 style amounts
        sa.Column("amount0_in", postgresql.NUMERIC(), nullable=True),
        sa.Column("amount1_in", postgresql.NUMERIC(), nullable=True),
        sa.Column("amount0_out", postgresql.NUMERIC(), nullable=True),
        sa.Column("amount1_out", postgresql.NUMERIC(), nullable=True),
        # V3 style amounts
        sa.Column("amount0", postgresql.NUMERIC(), nullable=True),
        sa.Column("amount1", postgresql.NUMERIC(), nullable=True),
        # V3 specific fields
        sa.Column("sqrt_price_x96", postgresql.NUMERIC(), nullable=True),
        sa.Column("liquidity", postgresql.NUMERIC(), nullable=True),
        sa.Column("tick", sa.INTEGER(), nullable=True),
        # Block information
        sa.Column("block_number", postgresql.BIGINT(), nullable=False),
        sa.Column("block_timestamp", postgresql.TIMESTAMP(), nullable=False),
        # Metadata
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("transaction_hash", "log_index"),
        if_not_exists=True,
    )

    # Create DEX mint events table
    op.create_table(
        "af_dex_mint_events",
        sa.Column("transaction_hash", postgresql.BYTEA(), nullable=False),
        sa.Column("log_index", sa.INTEGER(), nullable=False),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("sender", postgresql.BYTEA(), nullable=False),
        sa.Column("owner", postgresql.BYTEA(), nullable=True),
        sa.Column("amount0", postgresql.NUMERIC(), nullable=False),
        sa.Column("amount1", postgresql.NUMERIC(), nullable=False),
        # V3 specific fields
        sa.Column("tick_lower", sa.INTEGER(), nullable=True),
        sa.Column("tick_upper", sa.INTEGER(), nullable=True),
        sa.Column("amount", postgresql.NUMERIC(), nullable=True),
        # Block information
        sa.Column("block_number", postgresql.BIGINT(), nullable=False),
        sa.Column("block_timestamp", postgresql.TIMESTAMP(), nullable=False),
        # Metadata
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("transaction_hash", "log_index"),
        if_not_exists=True,
    )

    # Create DEX burn events table
    op.create_table(
        "af_dex_burn_events",
        sa.Column("transaction_hash", postgresql.BYTEA(), nullable=False),
        sa.Column("log_index", sa.INTEGER(), nullable=False),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("sender", postgresql.BYTEA(), nullable=False),
        sa.Column("to_address", postgresql.BYTEA(), nullable=True),
        sa.Column("owner", postgresql.BYTEA(), nullable=True),
        sa.Column("amount0", postgresql.NUMERIC(), nullable=False),
        sa.Column("amount1", postgresql.NUMERIC(), nullable=False),
        # V3 specific fields
        sa.Column("tick_lower", sa.INTEGER(), nullable=True),
        sa.Column("tick_upper", sa.INTEGER(), nullable=True),
        sa.Column("amount", postgresql.NUMERIC(), nullable=True),
        # Block information
        sa.Column("block_number", postgresql.BIGINT(), nullable=False),
        sa.Column("block_timestamp", postgresql.TIMESTAMP(), nullable=False),
        # Metadata
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("transaction_hash", "log_index"),
        if_not_exists=True,
    )

    # Create DEX pair created events table
    op.create_table(
        "af_dex_pair_created_events",
        sa.Column("transaction_hash", postgresql.BYTEA(), nullable=False),
        sa.Column("log_index", sa.INTEGER(), nullable=False),
        sa.Column("factory_address", postgresql.BYTEA(), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False, default="pair_created"),
        sa.Column("token0", postgresql.BYTEA(), nullable=False),
        sa.Column("token1", postgresql.BYTEA(), nullable=False),
        sa.Column("pair_address", postgresql.BYTEA(), nullable=False),
        sa.Column("pair_index", sa.INTEGER(), nullable=False),
        # Block information
        sa.Column("block_number", postgresql.BIGINT(), nullable=False),
        sa.Column("block_timestamp", postgresql.TIMESTAMP(), nullable=False),
        # Metadata
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("transaction_hash", "log_index"),
        if_not_exists=True,
    )

    # Create indexes for better query performance
    op.create_index(
        "idx_dex_swap_events_pool_address",
        "af_dex_swap_events",
        ["pool_address"],
        if_not_exists=True,
    )
    op.create_index(
        "idx_dex_swap_events_block_timestamp",
        "af_dex_swap_events",
        ["block_timestamp"],
        if_not_exists=True,
    )
    op.create_index(
        "idx_dex_swap_events_event_type",
        "af_dex_swap_events",
        ["event_type"],
        if_not_exists=True,
    )

    op.create_index(
        "idx_dex_mint_events_pool_address",
        "af_dex_mint_events",
        ["pool_address"],
        if_not_exists=True,
    )
    op.create_index(
        "idx_dex_mint_events_block_timestamp",
        "af_dex_mint_events",
        ["block_timestamp"],
        if_not_exists=True,
    )

    op.create_index(
        "idx_dex_burn_events_pool_address",
        "af_dex_burn_events",
        ["pool_address"],
        if_not_exists=True,
    )
    op.create_index(
        "idx_dex_burn_events_block_timestamp",
        "af_dex_burn_events",
        ["block_timestamp"],
        if_not_exists=True,
    )

    op.create_index(
        "idx_dex_pair_created_events_factory_address",
        "af_dex_pair_created_events",
        ["factory_address"],
        if_not_exists=True,
    )
    op.create_index(
        "idx_dex_pair_created_events_pair_address",
        "af_dex_pair_created_events",
        ["pair_address"],
        if_not_exists=True,
    )
    op.create_index(
        "idx_dex_pair_created_events_tokens",
        "af_dex_pair_created_events",
        ["token0", "token1"],
        if_not_exists=True,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_dex_pair_created_events_tokens", if_exists=True)
    op.drop_index("idx_dex_pair_created_events_pair_address", if_exists=True)
    op.drop_index("idx_dex_pair_created_events_factory_address", if_exists=True)
    op.drop_index("idx_dex_burn_events_block_timestamp", if_exists=True)
    op.drop_index("idx_dex_burn_events_pool_address", if_exists=True)
    op.drop_index("idx_dex_mint_events_block_timestamp", if_exists=True)
    op.drop_index("idx_dex_mint_events_pool_address", if_exists=True)
    op.drop_index("idx_dex_swap_events_event_type", if_exists=True)
    op.drop_index("idx_dex_swap_events_block_timestamp", if_exists=True)
    op.drop_index("idx_dex_swap_events_pool_address", if_exists=True)

    # Drop tables
    op.drop_table("af_dex_pair_created_events", if_exists=True)
    op.drop_table("af_dex_burn_events", if_exists=True)
    op.drop_table("af_dex_mint_events", if_exists=True)
    op.drop_table("af_dex_swap_events", if_exists=True) 