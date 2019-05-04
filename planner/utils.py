from collections import defaultdict
import logging

from planner import date_util
from planner.db import create_engine_and_metadata
from planner.db.airports import AirportsModel
from planner.db.fr_routes import FRRouteModel
from planner.db.miles import MilesModel
from planner.graph import RouteGraph

logger = logging.getLogger()


def group_by_key(routes: list, grouping_key: str) -> dict:
    tmp = defaultdict(list)
    for route in routes:
        tmp[route[grouping_key]].append(route)
    results = dict()
    for key, values in tmp.items():
        results[key] = sorted(values, key=lambda x: x['departure_time'])
    return results


class DataLoader:

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
                try:
                    flight = dict(
                        flight_number=route['flight_number'],
                        departure=route['departure'],
                        departure_time=date_util.parse_time(route['departure_time']),
                        arrival=route['arrival'],
                        arrival_time=date_util.parse_time(route['arrival_time']),
                        reward=self.get_reward(route['departure'], route['arrival']))
                except Exception:
                    logger.error('Can\'t build route: %s' % route)
                graph.add_edge(route['departure'], flight)
        nodes = graph.export()
        logger.info('Graph Nodes: %d, Total Edge: %d' % (len(nodes), sum([len(x) for x in nodes.values()])))
        return nodes
