from itertools import groupby
from collections import defaultdict
from typing import List

from planner.graph import RouteGraph


class Walker:

    def __init__(self, route: RouteGraph, init_flight: dict):
        self._route = route
        self._end_of_walk = False
        self._history_flight_number = {init_flight['flight_number']}

        self._start_airport = init_flight['arrival']
        self._plans = defaultdict(list)
        self._plans[self._start_airport].append(init_flight)

    @property
    def plans(self) -> list:
        return dict(self._plans)

    def _is_taken(self, last_flight: dict, next_flight: dict) -> bool:
        if last_flight['flight_number'] in self._history_flight_number or next_flight['flight_number'] in self._history_flight_number:
            print('Repeated Flight. End of {} Route '.format(self._start_airport))
            return True
        return False

    def _is_within_current_day(self, last_flight: dict, next_flight: dict) -> bool:
        if last_flight['arrival_time'] < next_flight['departure_time']:
            return True
        print(last_flight['departure_time'], next_flight['arrival_time'])
        print('Flight limited. End of {} Route '.format(self._start_airport))
        return False

    @staticmethod
    def _is_next_flight(last_flight: dict, next_flight: dict) -> bool:
        return last_flight['arrival_time'] < next_flight['departure_time']

    def _is_exit(self) -> bool:
        for airport, paths in self.plans.items():
            if len(paths) > 20:
                print('Unexpected Flight limit. End of {} Route'.format(airport))
                return True
        return False

    def filter_choices(self, routes: List[dict], last_flight: dict) -> dict:
        results = dict()
        for destination, flights in groupby(routes, key=lambda x: x['arrival']):
            for flight in sorted(flights, key=lambda x: x['departure_time']):
                if self._is_next_flight(last_flight, flight):
                    if self._is_within_current_day(last_flight, flight):
                        if self._is_taken(last_flight, flight):
                            results[destination] = flight
                            break
        return results

    def _select(self, choices: dict) -> dict:
        for destination, next_flight in choices.items():
            if self._is_exit():
                self._end_of_walk = True
            else:
                self._plans[destination].append(next_flight)

    def walk(self):
        counter = 1
        while not self._end_of_walk:
            print('Walk from {}, Loop: {}'.format(self._start_airport, counter))
            plans = self._plans.copy()
            for airport, flights in plans.items():
                last_flight = sorted(flights, key=lambda x: x['arrival_time'])[-1]
                routes = self._route.get(airport)

                # No Options
                if not routes:
                    self._end_of_walk = True
                    break

                # Narrow down choices
                possible_choices = self.filter_choices(routes, last_flight)
                print(possible_choices)
                if not possible_choices:
                    self._end_of_walk = True
                    break

                # walk
                self._select(possible_choices)
                counter += 1
