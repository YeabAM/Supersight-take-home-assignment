from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'

    device_id = Column(String(50), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship to metrics
    metrics = relationship("HourlyMetric", back_populates="device")

class HourlyMetric(Base):
    __tablename__ = 'hourly_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), ForeignKey('devices.device_id'), nullable=False)
    hour = Column(TIMESTAMP, nullable=False)
    people_in = Column(Integer, nullable=False, default=0)
    people_out = Column(Integer, nullable=False, default=0)
    net_flow = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationship to device
    device = relationship("Device", back_populates="metrics")

    # Unique constraint
    __table_args__ = (
        Index('idx_hourly_device_hour', 'device_id', 'hour'),
        Index('idx_hourly_hour', 'hour'),
        UniqueConstraint('device_id', 'hour', name='uq_device_hour')
    )