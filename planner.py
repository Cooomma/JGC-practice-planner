import json
import logging

from fire import Fire
from planner import date_util
from planner import utils
from planner.walker import Walker

logging.basicConfig(
    format='%(asctime)s- %(levelname)s - %(module)s.%(funcName)s - %(lineno)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger()


class CommandLine:

    def __init__(self, db_username: str, db_passwd: str, db_host: str = '10.0.1.6'):
        self.utils = utils.DataLoader(db_username, db_passwd, db_host)
        self.route = self.utils.build_graph()

    def show_graph(self):
        self.graph = self.utils.build_graph()
        for airport, flights in self.graph.items():
            print(airport, flights)
            print('\n')

    def plan(self, start_from: str = 'HND', start_time: str = '05:00:00', min_transit_time: int = 30, pratice_days: int = 1, top_k=10):
        results = dict()
        logger.info('Simulating Day 1')
        init_day_plans = Walker(route=self.route,
                                start_airport=start_from,
                                start_time=date_util.parse_time(start_time),
                                min_transit_time=min_transit_time).walk(top_k=top_k)
        results['1'] = {start_from: init_day_plans}
        existed_airport_routes = {start_from: init_day_plans}
        for day in range(2, pratice_days+1):
            logger.info('Simulating Day %s' % day)
            results[str(day)] = dict()
            for arrived_airport in {plan.airports[-1] for plan in init_day_plans}:
                existed_result = existed_airport_routes.get(arrived_airport)
                if existed_result:
                    results[str(day)][arrived_airport] = existed_result
                else:
                    following_plans = Walker(route=self.route,
                                             start_airport=arrived_airport,
                                             start_time=date_util.parse_time(start_time),
                                             min_transit_time=min_transit_time).walk(top_k=top_k)
                    existed_airport_routes.update({arrived_airport: following_plans})
                    results[str(day)][arrived_airport] = following_plans

        utils.export(results)
        utils.most_fop_route(results)


if __name__ == "__main__":
    Fire(CommandLine)
