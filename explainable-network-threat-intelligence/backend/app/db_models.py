
from sqlalchemy import Column, Integer, String, Double, TIMESTAMP, ForeignKey, text
from app.database import Base


class NetworkFlow(Base):
    __tablename__ = "network_flows"

    flow_id = Column(Integer, primary_key=True, autoincrement=True)
    source_ip = Column(String(45))
    destination_ip = Column(String(45))
    source_port = Column(Integer)
    destination_port = Column(Integer)
    protocol = Column(String(20))
    flow_duration = Column(Double)
    total_fwd_packets = Column(Integer)
    total_bwd_packets = Column(Integer)
    flow_bytes_per_second = Column(Double)
    flow_packets_per_second = Column(Double)
    captured_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )


class AttackPrediction(Base):
    __tablename__ = "attack_predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    flow_id = Column(
        Integer,
        ForeignKey("network_flows.flow_id"),
        nullable=False
    )
    prediction = Column(Integer)
    label = Column(String(20))
    confidence = Column(Double)
    uncertainty = Column(Double)
    status = Column(String(50))
    predicted_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )
