from sqlalchemy import INTEGER, Column, PrimaryKeyConstraint, func, String
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.dex_events.domain.dex_events import DexPairCreatedEvent


class AfDexPairCreatedEvent(HemeraModel):
    __tablename__ = "af_dex_pair_created_events"
    
    # Primary keys
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)

    # Event identification
    factory_address = Column(BYTEA, nullable=False)
    event_type = Column(String(20), nullable=False, default="pair_created")
    
    # Token addresses
    token0 = Column(BYTEA, nullable=False)
    token1 = Column(BYTEA, nullable=False)
    
    # Pair information
    pair_address = Column(BYTEA, nullable=False)
    pair_index = Column(INTEGER, nullable=False)

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
                "domain": DexPairCreatedEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ] 