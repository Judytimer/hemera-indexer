from sqlalchemy import INTEGER, Column, PrimaryKeyConstraint, func, String
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.dex_events.domain.dex_events import DexSwapEvent


class AfDexSwapEvent(HemeraModel):
    __tablename__ = "af_dex_swap_events"
    
    # Primary keys
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)

    # Event identification
    pool_address = Column(BYTEA, nullable=False)
    event_type = Column(String(20), nullable=False)  # "swap_v2" or "swap_v3"
    
    # Address fields
    sender = Column(BYTEA, nullable=False)
    to_address = Column(BYTEA)
    
    # V2 style amounts
    amount0_in = Column(NUMERIC)
    amount1_in = Column(NUMERIC) 
    amount0_out = Column(NUMERIC)
    amount1_out = Column(NUMERIC)
    
    # V3 style amounts (can be negative)
    amount0 = Column(NUMERIC)
    amount1 = Column(NUMERIC)
    
    # V3 specific fields
    sqrt_price_x96 = Column(NUMERIC)
    liquidity = Column(NUMERIC)
    tick = Column(INTEGER)

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
                "domain": DexSwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ] 