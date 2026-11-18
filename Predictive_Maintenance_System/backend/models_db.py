from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PredictionRecord(Base):
    """
    Stores each machine prediction request and its outcome in MySQL.
    """
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_type = Column(String(10), nullable=False)
    air_temperature = Column(Float, nullable=False)
    process_temperature = Column(Float, nullable=False)
    rotational_speed = Column(Integer, nullable=False)
    torque = Column(Float, nullable=False)
    tool_wear = Column(Integer, nullable=False)

    prediction = Column(Integer, nullable=False)
    result = Column(String(50), nullable=False)
    failure_probability = Column(Float, nullable=False)
    model_name = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        created_iso = self.created_at.isoformat() if self.created_at else None
        return {
            "id": self.id,
            "machine_type": self.machine_type,
            "air_temperature": self.air_temperature,
            "process_temperature": self.process_temperature,
            "rotational_speed": self.rotational_speed,
            "torque": self.torque,
            "tool_wear": self.tool_wear,
            "prediction": self.prediction,
            "result": self.result,
            "failure_probability": self.failure_probability,
            "model_name": self.model_name,
            "created_at": created_iso,
            # 'time' is kept for full compatibility with frontend Dashboard components
            "time": created_iso,
        }

