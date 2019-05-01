import logging
from itertools import groupby
from collections import defaultdict
from typing import List
from pprint import pprint
from planner.graph import RouteGraph
from planner import utils

logger = logging.getLogger()


class Walker:

    def __init__(self, route: RouteGraph, init_flight: dict):
        self._route = route
        self._end_of_walk = False
        self._history_flights = dict()
        self._history_flights[init_flight['flight_number']] = init_flight

        self._start_airport = init_flight['arrival']
        self._plans = defaultdict(list)
        self._plans[self._start_airport].append(init_flight['flight_number'])
        self.path = [init_flight['departure'], init_flight['arrival']]
        self.cumulate_points = init_flight['reward']

    @property
    def plans(self) -> list:
        result = dict()
        for destination, flight_no in self._plans.items():
            result[destination] = list(map(self._history_flights.get, flight_no))
        return result

    def _is_taken(self, next_flight: dict) -> bool:
        if next_flight['flight_number'] in self._plans[self._start_airport]:
            logger.warning('%s is repeated flight. End of %s Route. Taken flighs %s' % (
                next_flight['flight_number'], self._start_airport, self._plans[self._start_airport]))
            return True
        return False

    def _is_within_current_day(self, last_flight: dict, next_flight: dict) -> bool:
        if last_flight['arrival_time'] < next_flight['departure_time']:
            return True
        logger.warning('Flight limited. End of %s Route ' % self._start_airport)
        return False

    def next_flight(self, last_flight: dict, furture_flights: list) -> bool:
        results = list()
        for flight in furture_flights:
            if flight['departure_time'] > last_flight['arrival_time'] and flight['arrival'] != self.path[-1]:
                results.append(flight)
        results.sort(key=lambda x: x['departure_time'])
        return results[0] if results else None

    def _is_exit(self) -> bool:
        for airport, paths in self.plans.items():
            if len(paths) > 24:
                logger.warn('Unexpected Flight limit. End of %s Route' % airport)
                return True
        return False

    def filter_choices(self, routes: List[dict], last_flight: dict) -> dict:
        results = dict()
        for destination, flights in utils.group_by_key(routes=routes, grouping_key='departure').items():
            next_flight = self.next_flight(last_flight, flights)
            logger.debug('Flight Candidate: %s', next_flight)
            if next_flight:
                if not self._is_taken(next_flight):
                    if self._is_within_current_day(last_flight, next_flight):
                        results[destination] = next_flight
                        break
        return results

    def _select(self, choices: dict) -> dict:
        for destination, next_flight in choices.items():
            if self._is_exit():
                self._end_of_walk = True
            else:
                self._history_flights[next_flight['flight_number']] = next_flight
                self._plans[destination].append(next_flight['flight_number'])
                self.path.append(next_flight['arrival'])
                self.cumulate_points += next_flight['reward']
                break

    def walk(self):
        counter = 1
        while not self._end_of_walk:
            logger.info('Walk from %s, Loop: %s' % (self._start_airport, counter))
            plans = self._plans.copy()
            for airport, flights in plans.items():
                last_flight = self._history_flights[flights[-1]]
                routes = self._route.get(airport)

                # No Options
                if not routes:
                    self._end_of_walk = True
                    break

                logger.info('Routes: %s' % len(routes))
                # Narrow down choices
                possible_choices = self.filter_choices(routes, last_flight)
                logger.info('Possible Choices: %s' % len(possible_choices))
                logger.debug('All Possible Choices: %s' % possible_choices)
                if not possible_choices:
                    self._end_of_walk = True
                    break

                # walk
                self._select(possible_choices)
                counter += 1
