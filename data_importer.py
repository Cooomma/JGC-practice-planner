import json
import os
import traceback

from fire import Fire
import requests
from planner.db import create_engine_and_metadata
from planner.db.routes import RouteModel
from planner.db.airports import AirportsModel
from planner.db.miles import MilesModel


class CommandLine:

    def __init__(self, db_username: str, db_passwd: str, api_key: str):
        engine, metadata = create_engine_and_metadata('10.0.1.4', db_username, db_passwd, 'flights')
        self.route_db = RouteModel(engine, metadata, role='writer')
        self.airport_db = AirportsModel(engine, metadata, role='writer')
        self.miles_db = MilesModel(engine, metadata, role='writer')
        self.api_key = api_key

    @staticmethod
    def rename_route(record: dict) -> dict:
        return dict(
            flight_number=int(record['flightNumber']),
            airline_iata=record['airlineIata'],
            airline_icao=record['airlineIcao'],
            departure_iata=record['departureIata'],
            departure_icao=record['departureIcao'],
            departure_terminal=record['departureTerminal'],
            departure_time=record['departureTime'],
            arrival_iata=record['arrivalIata'],
            arrival_icao=record['arrivalIcao'],
            arrival_terminal=record['arrivalTerminal'],
            arrival_time=record['arrivalTime'],
            reg_code=record['regNumber'])

    @staticmethod
    def rename_airport(record: dict) -> dict:
        return dict(
            id=int(record['airportId']),
            name=record['nameAirport'],
            iata_code=record['codeIataAirport'],
            icao_code=record['codeIcaoAirport'],
            translations_name=record['nameTranslations'],
            latitude=float(record['latitudeAirport']),
            longitude=float(record['longitudeAirport']),
            geo_name_id=record['geonameId'],
            timezone=record['timezone'],
            gmt=int(record['GMT']),
            country=record['nameCountry'],
            country_code_iso2=record['codeIso2Country'],
            city_iata_code=record['codeIataCity'])

    def parse_airport_data_into_db(self, country_code: str):
        for airport in requests.get(url=' https://aviation-edge.com/v2/public/airportDatabase', params=dict(key=self.api_key, codeIso2Country=country_code)).json():
            try:
                self.airport_db.raw_insert(self.rename_airport(airport))
            except:
                print(airport)
                print(traceback.format_exc())

    def parse_route_data_into_db(self, airline_iata: str):
        for route in requests.get(url=' http://aviation-edge.com/v2/public/routes', params=dict(key=self.api_key, airlineIata=airline_iata)).json():
            try:
                self.route_db.raw_insert(self.rename_route(route))
            except:
                print(route)
                print(traceback.format_exc())

    def parse_miles_data_into_db(self):
        with open(os.path.abspath('./datas/Miles.txt'), 'r') as reader:
            for line in reader.readlines():
                from_city, to_city, miles = line.split('|')
                self.miles_db.raw_insert(
                    dict(from_city_iata_code=from_city, to_city_iata_code=to_city, miles=int(miles)))
                self.miles_db.raw_insert(
                    dict(from_city_iata_code=to_city, to_city_iata_code=from_city, miles=int(miles)))

    def export_db(self):
        with open('./datas/jmb_miles.json', 'w') as writer:
            for miles in self.miles_db.export_all():
                writer.write(json.dumps(miles, ensure_ascii=False, sort_keys=True))
                writer.write('\n')

        with open('./datas/jl_routes.json', 'w') as writer:
            for route in self.route_db.export_all():
                writer.write(json.dumps(route, ensure_ascii=False, sort_keys=True))
                writer.write('\n')

        with open('./datas/jp_airports.json', 'w') as writer:
            for airport in self.airport_db.export_all():
                airport['latitude'] = float(airport['latitude'])
                airport['longitude'] = float(airport['longitude'])
                writer.write(json.dumps(airport, ensure_ascii=False, sort_keys=True))
                writer.write('\n')


if __name__ == "__main__":
    Fire(CommandLine)
