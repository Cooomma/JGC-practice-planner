import time
from typing import List, Generator

from planner.db import BaseModel
from sqlalchemy import INT, Column, String, Table, and_, JSON, DECIMAL
from sqlalchemy.sql.expression import select


class AirportsModel(BaseModel):

    def __init__(self, engine, metadata, role='reader'):
        table = Table(
            'airports',
            metadata,
            Column('id', INT, primary_key=True),
            Column('name', String(255)),
            Column('iata_code', String(255)),
            Column('icao_code', String(255)),
            Column('translations_name', String(255)),
            Column('latitude', DECIMAL),
            Column('longitude', DECIMAL),
            Column('geo_name_id', INT),
            Column('timezone', String(255)),
            Column('gmt', INT),
            Column('country', String(255)),
            Column('country_code_iso2', String(255)),
            Column('city_iata_code', String(255)),
            Column('updated_at', INT),
            extend_existing=True)
        super().__init__(engine, metadata, table, role)

    def export_all(self) -> Generator[dict, None, None]:
        cursor = self.execute(select(self.table.columns))
        row = cursor.fetchone()
        while row:
            yield dict(zip([col.key for col in self.table.columns], row))
            row = cursor.fetchone()

    def get_city_iata_code(self, airport_iata: str) -> str:
        stmt = select([self.table.c.city_iata_code]).where(
            and_(self.table.c.iata_code == airport_iata))
        return self.execute(stmt).fetchone().city_iata_code

    def get_airport_by_country_code(self, country_code: str) -> List[dict]:
        stmt = select([self.table.c.id, self.table.c.name,
                       self.table.c.iata_code, self.table.c.timezone,
                       self.table.c.gmt, self.table.c.city_iata_code]).where(and_(self.table.c.country_code_iso2 == country_code))
        cursor = self.execute(stmt)
        row = cursor.fetchone()
        while row:
            yield dict(
                id=row.id,
                name=row.name,
                iata_code=row.iata_code,
                timezone=row.timezone,
                gmt=row.gmt,
                city_iata_code=row.city_iata_code)
            row = cursor.fetchone()
