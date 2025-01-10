import datetime
from dataclasses import dataclass
from typing import Generator

import firebase_admin
from firebase_admin import firestore
from firebase_admin.credentials import Certificate

from external_source import ExternalSourceService


@dataclass
class SensorData:
    temperatura: float  # Celsius
    umidade_ar: float  # %
    umidade_solo: float  # %
    data_coleta: datetime.datetime


class SensorSource(ExternalSourceService):
    def __init__(self, cert_filename: str, data_collection="DadosEmissor1"):
        self.cert = Certificate(cert_filename)
        self.app = firebase_admin.initialize_app(self.cert)
        self.db = firestore.client()
        self.collection = self.db.collection(data_collection)

    def _format_data(self, raw_document: dict):
        return SensorData(
            temperatura=raw_document.get("Temperatura"),
            umidade_ar=raw_document.get("UmidadeAr"),
            umidade_solo=raw_document.get("UmidadeSolo"),
            data_coleta=datetime.datetime.fromtimestamp(raw_document.get("timestamp").timestamp()),
        )

    def get_data(self, date_range: tuple[datetime.datetime]) -> Generator[None, None, SensorData]:
        start_date, end_date = date_range

        query = self.collection.where("timestamp", ">=", start_date).where("timestamp", "<=", end_date)
        all_documents = query.stream()

        for document in all_documents:
            yield self._format_data(document)

    def get_data_count(self):
        return self.collection.count()


if __name__ == "__main__":
    now = datetime.datetime.now()
    old = datetime.datetime.now() - datetime.timedelta(weeks=500)

    ec = SensorSource("./external/cred.json")
