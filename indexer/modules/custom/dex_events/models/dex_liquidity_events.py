from sqlalchemy import INTEGER, Column, PrimaryKeyConstraint, func, String
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.dex_events.domain.dex_events import DexMintEvent, DexBurnEvent


class AfDexMintEvent(HemeraModel):
    __tablename__ = "af_dex_mint_events"
    
    # Primary keys
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)

    # Event identification
    pool_address = Column(BYTEA, nullable=False)
    event_type = Column(String(20), nullable=False)  # "mint_v2" or "mint_v3"
    
    # Address fields
    sender = Column(BYTEA, nullable=False)
    owner = Column(BYTEA)  # V3 style
    
    # Token amounts
    amount0 = Column(NUMERIC, nullable=False)
    amount1 = Column(NUMERIC, nullable=False)
    
    # V3 specific fields
    tick_lower = Column(INTEGER)
    tick_upper = Column(INTEGER)
    amount = Column(NUMERIC)  # V3 liquidity amount

    # Block information
    block_number = Column(BIGINT, nullable=False)
    block_timestamp = Column(TIMESTAMP, nullable=False)

    # Metadata
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": DexMintEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


class AfDexBurnEvent(HemeraModel):
    __tablename__ = "af_dex_burn_events"
    
    # Primary keys
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)

    # Event identification
    pool_address = Column(BYTEA, nullable=False)
    event_type = Column(String(20), nullable=False)  # "burn_v2" or "burn_v3"
    
    # Address fields
    sender = Column(BYTEA, nullable=False)
    to_address = Column(BYTEA)  # V2 style
    owner = Column(BYTEA)  # V3 style
    
    # Token amounts
    amount0 = Column(NUMERIC, nullable=False)
    amount1 = Column(NUMERIC, nullable=False)
    
    # V3 specific fields
    tick_lower = Column(INTEGER)
    tick_upper = Column(INTEGER)
    amount = Column(NUMERIC)  # V3 liquidity amount

    # Block information
    block_number = Column(BIGINT, nullable=False)
    block_timestamp = Column(TIMESTAMP, nullable=False)

    # Metadata
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": DexBurnEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ] 