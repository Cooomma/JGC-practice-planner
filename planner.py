import logging

from fire import Fire
from planner import date_util
from planner.utils import DataLoader
from planner.walker import Walker

logging.basicConfig(
    format='%(asctime)s- %(levelname)s - %(module)s.%(funcName)s - %(lineno)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger()


class CommandLine:

    def __init__(self, db_username: str, db_passwd: str, db_host: str = '10.0.1.6'):
        self.utils = DataLoader(db_username, db_passwd, db_host)

    def show_graph(self):
        self.graph = self.utils.build_graph()
        for airport, flights in self.graph.items():
            print(airport, flights)
            print('\n')

    def plan(self, start_from: str = 'HND', start_time: str = '05:00:00', min_transit_time: int = 30, pratice_days: int = 1, top_k=10):
        walker = Walker(route=self.utils.build_graph(),
                        start_airport=start_from,
                        start_time=date_util.parse_time(start_time),
                        min_transit_time=min_transit_time)

        for plan in walker.walk(top_k=top_k):
            print(plan.to_human())


if __name__ == "__main__":
    Fire(CommandLine)
