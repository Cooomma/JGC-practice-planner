from collections import defaultdict
import logging
from pprint import pprint
import traceback

from fire import Fire
from planner import date_util
from planner.utils import Utils
from planner.walker import Walker

logger = logging.getLogger()


class CommandLine:

    def __init__(self, db_username: str, db_passwd: str):
        self.utils = Utils(db_username, db_passwd)
        self.graph = self.utils.build_graph()

    def show_graph(self):
        for airport, flights in self.graph.items():
            print(airport, flights)
            print('\n')

    def plan(self, start_from: str = 'HND', start_time: str = '05:00:00', duration: int = 1):
        route_graph = self.graph
        first_start_time = date_util.parse_time(start_time)
        init_step = dict()

        # First Move
        for next_stop, flight in self.utils.get_all_latest_unique_stop_flights_after_arrival(route_graph.get(start_from), first_start_time).items():
            init_step[next_stop] = flight

        for airport, flight in init_step.items():
            print('FROM {} TO {} via {}'.format(start_from, airport, flight))
            walker = Walker(route_graph, flight)
            walker.walk()

            pprint(walker.plans)
            print('\n')

        # After all path generated
        '''
        # Calculate Rewards for routes
        result = dict()
        for start_point, flighs in flight_plans.values():
        result[start_point] = sum([x['reward'] for x in flighs])

        # best_route = sorted(result, key=lambda x: x.values())
        print(result)
        '''


if __name__ == "__main__":
    Fire(CommandLine)
