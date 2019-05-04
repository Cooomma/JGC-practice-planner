import copy
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from itertools import groupby
import logging
from pprint import pprint
from typing import List

from planner import utils
from planner.graph import FlightPlan, RouteGraph

logger = logging.getLogger()


class Walker:

    def __init__(self, route: RouteGraph, start_airport: str, start_time: datetime, min_transit_time: int):
        self._route = route
        self._end_of_walk = False
        self._minimum_transit_time = timedelta(seconds=min_transit_time)

        self._start_airport = start_airport
        self._start_time = start_time

        self._plans = list()

    def _is_connected(self, previous_flight: dict, next_flight: dict) -> bool:
        return previous_flight['arrival'] == next_flight['departure']

    def _is_within_current_day(self, current_time: datetime, next_flight: dict) -> bool:
        if current_time < next_flight['departure_time']:
            return True
        logger.warning('Flight limited. End of %s Route ' % self._start_airport)
        return False

    def _is_enough_transit_time(self, current_time: datetime, next_flight: dict) -> bool:
        return (current_time + self._minimum_transit_time) < next_flight['departure_time']

    @staticmethod
    def _is_exit(paths: list) -> bool:
        if len(paths) > 24:
            logger.warning('Unexpected Flight limit. End of %s Route')
            return True
        return False

    def _next_flights(self, current_airport: str, current_time: datetime) -> dict:
        results = defaultdict(list)
        routes = self._route.get(current_airport)
        logger.debug('%s of flights in %s' % (len(routes), current_airport))
        if routes:
            for destination, flights in utils.group_by_key(routes, grouping_key='arrival').items():
                for possible_flight in sorted(flights, key=lambda x: x['departure_time']):
                    if self._is_enough_transit_time(current_time, possible_flight) and self._is_within_current_day(current_time, possible_flight):
                        logger.debug('%s, possible flights: %s' % (destination, possible_flight))
                        results[destination].append(possible_flight)
                        break
        return dict(results)

    @staticmethod
    def _historial_paths(previous_airports: list):
        return '_'.join(previous_airports)

    def walk(self):
        simulating_paths = dict()

        for next_flights in self._next_flights(self._start_airport, self._start_time).values():
            flight_plan = FlightPlan(self._start_airport)
            flight_plan.add_route(next_flights[0])
            simulating_paths[self._historial_paths(flight_plan.airports)] = flight_plan

        is_continue = True
        counter = 0
        for airport_path, plan in simulating_paths.items():
            logger.debug('Airport: %s, Plans: %s' % (airport_path, plan.to_dict()))

        while is_continue:
            counter += 1
            logger.info('Loop: %s. Current Number of  Simulating Paths %s' % (counter, len(simulating_paths.keys())))

            current_simulating_path = copy.deepcopy(simulating_paths)

            for path_key, flight_plan in current_simulating_path.items():
                if flight_plan.is_end:
                    break

                last_flight = flight_plan.flights[-1]
                current_airport = last_flight['arrival']
                current_time = last_flight['arrival_time']

                del simulating_paths[path_key]
                for next_flights in self._next_flights(current_airport, current_time).values():
                    if next_flights:
                        for next_flight in next_flights:
                            if self._is_connected(last_flight, next_flight):
                                new_flight_plan = copy.deepcopy(flight_plan)
                                simulating_paths[self._historial_paths(
                                    new_flight_plan.airports)] = new_flight_plan.add_route(next_flight)
                    else:
                        flight_plan.is_end = True
                logger.debug('Airport: %s, Plans: %s' % (path_key, flight_plan.to_dict()))

            is_continue = not all([plan.is_end for plan in current_simulating_path.values()])
            logger.info(
                'Loop: %s End. Current Simulating Paths %s, Continues?: %s' %
                (counter,
                 dict(Counter([plan.is_end for plan in current_simulating_path.values()])),
                 is_continue))

            if not is_continue:
                for path, plan in simulating_paths.items():
                    print(path)
