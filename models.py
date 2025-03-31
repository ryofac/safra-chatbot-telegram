from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TemperatureReading(Base):
    __tablename__ = "temperature_reading"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, nullable=False)
    temperature = Column(Float, nullable=False)
    moisture = Column(Float, nullable=False, default=0.0)
    gas_level = Column(Float, nullable=False, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    class Config:
        orm_mode = True
