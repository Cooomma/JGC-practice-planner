from collections import defaultdict


class RouteGraph:

    def __init__(self):
        '''
        Graph would be route table. {departure, arrivals}
        '''
        self._graph = defaultdict(list)

    def add_edge(self, departure: str, arrival: dict):
        self._graph[departure].append(arrival)

    def export(self):
        result = dict()
        for key, value in self._graph.items():
            result[key] = sorted(value, key=lambda x: x['departure_time'])
        return self._graph


class FlightPlan:

    def __init__(self, initial_airport: str):
        self._is_end = False
        self._flights = []
        self._airports = [initial_airport]
        self._previous_airport = ''
        self._current_airport = ''

    @property
    def is_end(self):
        return self._is_end

    @is_end.setter
    def is_end(self, value: bool):
        self._is_end = value

    @property
    def flights(self):
        return self._flights

    @property
    def airports(self):
        return self._airports

    @property
    def previous_airport(self):
        return self._previous_airport

    @property
    def current_airport(self):
        return self._current_airport

    @property
    def fop(self):
        return sum([flight['reward'] for flight in self._flights])

    def add_route(self, flight: dict):
        self._airports.append(flight['arrival'])
        self._flights.append(flight)
        self._previous_airport = flight['departure']
        self._current_airport = flight['arrival']
        return self

    def to_dict(self):
        return dict(airports=self._airports, flights=self._flights)
