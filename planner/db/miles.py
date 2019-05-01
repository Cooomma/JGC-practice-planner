import time
from typing import List, Generator

from planner.db import BaseModel
from sqlalchemy import INT, Column, String, Table, and_, JSON, DECIMAL
from sqlalchemy.sql.expression import select


class MilesModel(BaseModel):

    def __init__(self, engine, metadata, role='reader'):
        table = Table(
            'miles',
            metadata,
            Column('id', INT, primary_key=True, autoincrement=True),
            Column('from_city_iata_code', String(8)),
            Column('to_city_iata_code', String(8)),
            Column('miles', INT),
            Column('updated_at', INT),
            extend_existing=True)
        super().__init__(engine, metadata, table, role)

    def export_all(self) -> Generator[dict, None, None]:
        cursor = self.execute(select(self.table.columns))
        row = cursor.fetchone()
        while row:
            yield dict(zip([col.key for col in self.table.columns], row))
            row = cursor.fetchone()

    def get_miles(self, from_city_iata: str, to_city_iata: str) -> int:
        stmt = select([self.table.c.miles]).where(
            and_(self.table.c.from_city_iata_code == from_city_iata,
                 self.table.c.to_city_iata_code == to_city_iata_code))
        return self.execute(stmt).fetchone().miles
