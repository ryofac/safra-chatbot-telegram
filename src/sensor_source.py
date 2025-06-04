import datetime
from dataclasses import dataclass
from typing import Generator

import config
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, select

from models import TemperatureReading, Base


@dataclass
class SensorData:
    temperature: float  # Celsius
    moisture: float  # %
    gas_level: float  # %
    data_coleta: datetime.datetime


class SensorSource:
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL)
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(self.engine)

    def _format_data(self, row: TemperatureReading) -> SensorData:
        return SensorData(
            temperature=row.temperature,
            moisture=row.moisture,
            gas_level=row.gas_level,
            data_coleta=row.timestamp,
        )

    def get_data(self, date_range: tuple[datetime.datetime, datetime.datetime]) -> Generator[SensorData, None, None]:
        start_date, end_date = date_range
        
        with self.session() as session:
            query = select(TemperatureReading).where(
                TemperatureReading.timestamp >= start_date,
                TemperatureReading.timestamp <= end_date
            )
            result = session.execute(query).scalars()

            for row in result:
                yield self._format_data(row)

    def get_data_count(self) -> int:
        with self.session() as session:
            query = select(TemperatureReading).count()
            return session.execute(query).scalar()
