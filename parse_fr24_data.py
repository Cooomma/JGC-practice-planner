import time
from datetime import datetime
import json
import os
import traceback

import pytz
from pytz import timezone
from fire import Fire
from pprint import pprint
import requests
from planner.db import create_engine_and_metadata
from planner.db.routes import RouteModel
from planner.db.airports import AirportsModel
from planner.db.fr_routes import FRRouteModel
from planner.db.miles import MilesModel


class CommandLine:

    def __init__(self, db_username: str, db_passwd: str, api_key: str = None):
        engine, metadata = create_engine_and_metadata('10.0.1.4', db_username, db_passwd, 'flights')
        self.route_db = FRRouteModel(engine, metadata, role='writer')
        # self.airport_db = AirportsModel(engine, metadata, role='writer')
        # self.miles_db = MilesModel(engine, metadata, role='writer')
        self.api_key = api_key

    @staticmethod
    def rename_route(record: dict) -> dict:
        return dict(
            flight_number=record['flightNumber'],
            departure_iata=record['departureIata'],
            departure_time=record['departureTime'],
            arrival_iata=record['arrivalIata'],
            arrival_time=record['arrivalTime'])

    @staticmethod
    def unixts_to_jst(ts: int) -> str:
        return datetime.strftime(datetime.fromtimestamp(ts).astimezone(timezone('Asia/Tokyo')), '%H:%M:%S')

    def parse_fr24_data(self):
        departure, arrival = dict(), dict()
        records = list()
        for file in os.listdir('./datas/fr24'):
            path = os.path.abspath(os.path.join('./datas/fr24/', file))
            with open(path, 'r') as reader:
                records.extend([json.loads(line) for line in reader.readlines() if line])
        for record in records:
            # print(record)
            # print(record['arrivals']['Japan']['airports'])
            for airport, flight_infos in record['arrivals']['Japan']['airports'].items():
                for flight_number, flight_detail in flight_infos['flights'].items():
                    for info in flight_detail['utc'].values():
                        arrival[flight_number] = dict(
                            arrival_time=self.unixts_to_jst(info['timestamp']),
                            departure_iata=airport)

            for airport, flight_infos in record['departures']['Japan']['airports'].items():
                for flight_number, flight_detail in flight_infos['flights'].items():
                    for info in flight_detail['utc'].values():
                        departure[flight_number] = dict(
                            departure_time=self.unixts_to_jst(info['timestamp']),
                            arrival_iata=airport)

        routes = dict()
        for departure_flight_number, info in departure.items():
            arrival_info = arrival.get(departure_flight_number)
            if arrival_info:
                info.update(arrival_info)
            routes[departure_flight_number] = info

        for arrival_flight_number, info in arrival.items():
            departure_info = departure.get(arrival_flight_number)
            if departure_info:
                info.update(departure_info)
            routes[arrival_flight_number] = info

        for flight_number, info in routes.items():
            line = dict(
                arrival_iata=info.get('arrival_iata'),
                arrival_time=info.get('arrival_time'),
                departure_iata=info.get('departure_iata'),
                departure_time=info.get('departure_time'),
                flight_number=flight_number)
            self.route_db.raw_insert(line)


if __name__ == "__main__":
    Fire(CommandLine)
