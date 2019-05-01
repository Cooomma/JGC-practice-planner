import time
from typing import List, Generator

from planner.db import BaseModel
from sqlalchemy import INT, Column, String, Table, and_, JSON, BOOLEAN
from sqlalchemy.sql.expression import select, asc


class FRRouteModel(BaseModel):

    def __init__(self, engine, metadata, role='reader'):
        table = Table(
            'fr_routes',
            metadata,
            Column('flight_number', String(64), primary_key=True),
            Column('departure_iata', String(255)),
            Column('departure_time', String(255)),
            Column('arrival_iata', String(255)),
            Column('arrival_time', String(255)),
            Column('domestic', BOOLEAN),
            Column('updated_at', INT),
            extend_existing=True)
        super().__init__(engine, metadata, table, role)

    def export_all(self) -> Generator[dict, None, None]:
        cursor = self.execute(select(self.table.columns))
        row = cursor.fetchone()
        while row:
            yield dict(zip([col.key for col in self.table.columns], row))
            row = cursor.fetchone()

    def get_routes(self, departure_iata: str) -> List[dict]:
        stmt = select([self.table.c.flight_number,
                       self.table.c.departure_iata, self.table.c.arrival_iata,
                       self.table.c.departure_time, self.table.c.arrival_time])\
            .where(and_(self.table.c.departure_iata == departure_iata)) \
            .order_by(asc(self.table.c.departure_time))
        cursor = self.execute(stmt)
        row = cursor.fetchone()
        while row:
            yield dict(flight_number=row.flight_number, departure=row.departure_iata,
                       arrival=row.arrival_iata, departure_time=row.departure_time, arrival_time=row.arrival_time)
            row = cursor.fetchone()
