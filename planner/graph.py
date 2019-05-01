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
