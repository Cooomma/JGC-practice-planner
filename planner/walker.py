import copy
from datetime import datetime, timedelta
import logging

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
        routes = self._route.get(current_airport)
        results = dict()
        logger.debug('%s of flights in %s' % (len(routes), current_airport))
        for destination, flights in utils.group_by_key(routes, grouping_key='arrival', sort_by='departure_time').items():
            for optimal_flight in flights:
                if self._is_enough_transit_time(current_time, optimal_flight) and self._is_within_current_day(current_time, optimal_flight):
                    logger.debug('%s, possible flights: %s' % (destination, optimal_flight))
                    results[destination] = optimal_flight
                    break
        return dict(results)

    @staticmethod
    def _historial_paths(previous_airports: list):
        return '_'.join(previous_airports)

    def walk(self):
        simulating_paths = dict()

        for next_flight in self._next_flights(self._start_airport, self._start_time).values():
            flight_plan = FlightPlan(self._start_airport)
            flight_plan.add_route(next_flight)
            simulating_paths[self._historial_paths(flight_plan.airports)] = flight_plan

        is_continue = True
        counter = 0
        current_simulating_path = simulating_paths.copy()
        # for airport_path, plan in simulating_paths.items():
        #    logger.debug('Airport: %s, Plans: %s' % (airport_path, plan.to_dict()))

        while is_continue:
            counter += 1
            logger.info('Loop: %s. Current Number of  Simulating Paths %s' % (counter, len(simulating_paths.keys())))

            for path_key, flight_plan in current_simulating_path.items():

                last_flight = flight_plan.flights[-1]
                current_airport = last_flight['arrival']
                current_time = last_flight['arrival_time']

                next_flights = self._next_flights(current_airport, current_time).values()
                if next_flights:
                    for next_flight in next_flights:
                        if self._is_connected(last_flight, next_flight):
                            new_flight_plan = copy.deepcopy(flight_plan)
                            simulating_paths[self._historial_paths(
                                new_flight_plan.airports)] = new_flight_plan.add_route(next_flight)
                    is_continue = not all([plan.is_end for plan in current_simulating_path.values()])
                    logger.debug('Airport: %s, Plans: %s' % (path_key, flight_plan.to_dict()))
                    current_simulating_path = simulating_paths.copy()
                else:
                    is_continue = False

            logger.info(
                'Loop: %s End. Current Simulating Paths %s, Continues?: %s' %
                (counter, len(current_simulating_path.values()), is_continue))

        results = []
        for plan in simulating_paths.values():
            # results.append(dict(path=plan.airports, plan=plan, fop=plan.fop))
            results.append(plan)

        results.sort(key=lambda x: x.fop, reverse=True)
        best = results[:10]
        for plan in best:
            print(plan.to_human())
            print('\n')
