import time
from typing import List, Generator

from planner.db import BaseModel
from sqlalchemy import INT, Column, String, Table, and_, JSON
from sqlalchemy.sql.expression import select


class RouteModel(BaseModel):

    def __init__(self, engine, metadata, role='reader'):
        table = Table(
            'routes',
            metadata,
            Column('flight_number', INT, primary_key=True),
            Column('airline_iata', String(255)),
            Column('airline_icao', String(255)),
            Column('departure_iata', String(255)),
            Column('departure_icao', String(255)),
            Column('departure_terminal', String(255)),
            Column('departure_time', String(255)),
            Column('arrival_iata', String(255)),
            Column('arrival_icao', String(255)),
            Column('arrival_terminal', String(255)),
            Column('arrival_time', String(255)),
            Column('reg_code', JSON, nullable=True),
            Column('updated_at', INT),

            extend_existing=True)
        super().__init__(engine, metadata, table, role)

    def export_all(self) -> Generator[dict, None, None]:
        cursor = self.execute(select(self.table.columns))
        row = cursor.fetchone()
        while row:
            yield dict(zip([col.key for col in self.table.columns], row))
            row = cursor.fetchone()

    def get_routes(self, departure_iata: str, arrival_iata: str) -> List[dict]:
        stmt = select([self.table.c.fligh_number,
                       self.table.c.departure_iata, self.table.c.arrival_iata,
                       self.table.c.departure_time, self.table.c.arrival_time])\
            .where(and_(self.table.c.departure_iata == departure_iata, self.table.c.arrival_iata == arrival_iata))
        result = []
        cursor = self.execute(stmt)
        row = cursor.fetchone()
        while row:
            result.append(dict(flight_number=row.fligh_number, departure_iata=row.departure_iata,
                               arrival_iata=row.arrival_iata, departure_time=row.departure_time, arrival_time=row.arrival_time))
            row = cursor.fetchone()
        return result
