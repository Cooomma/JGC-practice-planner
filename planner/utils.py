from collections import defaultdict
from datetime import datetime
import logging
from typing import List

from planner import date_util
from planner.db import create_engine_and_metadata
from planner.db.airports import AirportsModel
from planner.db.miles import MilesModel
from planner.db.fr_routes import FRRouteModel
from planner.graph import RouteGraph, FlightPlan


logger = logging.getLogger()


def group_by_key(routes: list, grouping_key: str) -> dict:
    result = defaultdict(list)
    for route in routes:
        result[route[grouping_key]].append(route)
    return result


class Utils:

    multiplier = 2
    bonus = 400

    def __init__(self, db_username: str, db_passwd: str, db_host: str):
        engine, metadata = create_engine_and_metadata(db_host, db_username, db_passwd, 'flights')
        self.route_db = FRRouteModel(engine, metadata, role='writer')
        self.airport_db = AirportsModel(engine, metadata, role='writer')
        self.miles_db = MilesModel(engine, metadata, role='writer')

    def get_reward(self, departure: str, arrival: str) -> int:
        departure = self.airport_db.get_city_iata_code(departure.upper())
        arrival = self.airport_db.get_city_iata_code(arrival.upper())
        miles = self.miles_db.get_miles(departure, arrival)
        if miles:
            return int(miles * self.multiplier + self.bonus)
        logger.error('No Miles Record. From %s to %s', departure, arrival)
        return 0

    def get_route(self, departure: str) -> dict:
        return self.route_db.get_routes(departure)

    def build_graph(self) -> dict:
        graph = RouteGraph()
        for airport in self.airport_db.get_airport_by_country_code('JP'):
            for route in self.route_db.get_routes(airport['iata_code']):
                if route:
                    try:
                        flight = dict(
                            flight_number=route['flight_number'],
                            departure=route['departure'],
                            departure_time=date_util.parse_time(route['departure_time']),
                            arrival=route['arrival'],
                            arrival_time=date_util.parse_time(route['arrival_time']),
                            reward=self.get_reward(route['departure'], route['arrival']))
                    except:
                        logger.error('Can\'t build route: %s' % route)
                    graph.add_edge(route['departure'], flight)
        nodes = graph.export()
        logger.info('Graph Nodes: %d, Total Edge: %d' % (len(nodes), sum([len(x) for x in nodes.values()])))
        return nodes

    def build_flight_plan(self):
        airports = [x for x in self.airport_db.get_airport_by_country_code('JP')]
        flight_plan = FlightPlan(len(airports))
        for airport in airports:
            for route in self.route_db.get_routes(airport['iata_code']):
                if route:
                    try:
                        flight = dict(
                            flight_number=route['flight_number'],
                            departure=route['departure'],
                            departure_time=date_util.parse_time(route['departure_time']),
                            arrival=route['arrival'],
                            arrival_time=date_util.parse_time(route['arrival_time']),
                            reward=self.get_reward(route['departure'], route['arrival']))
                    except:
                        logger.error('Can\'t build route: %s' % route)
                    flight_plan.add_flight(route['departure'], flight)

        flight_plan.topologicalSort()

    @staticmethod
    def get_all_latest_unique_stop_flights_after_arrival(flights: List[dict], arrival_time: datetime) -> dict:
        existed_stops = set()
        results = dict()

        for flight in sorted(flights, key=lambda x: x['departure_time']):
            arrival = flight['arrival']
            if arrival not in existed_stops and arrival_time < flight['departure_time']:
                results[arrival] = flight
            existed_stops.add(arrival)
        return results
