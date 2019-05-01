import time
import json
import os
import traceback

from fire import Fire
import requests
from planner.db import create_engine_and_metadata
from planner.db.routes import RouteModel
from planner.db.airports import AirportsModel
from planner.db.miles import MilesModel
from planner.db.fr_routes import FRRouteModel


fr24_header = {
    'accept-encoding': "gzip, deflate, br",
    'x-fetch': "true",
    'accept-language': "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
    'content-type': "application/json",
    'accept': "*/*",
    'referer': "https://www.flightradar24.com/data/airlines/jl-jal/routes",
    'authority': "www.flightradar24.com",
    'cookie': "__cfduid=dd028cbef677259b9597e9691ba2837ad1552826955; __utmz=177865842.1552826958.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); cookie_law_consent=1; _frr=1; _frc=LeoxwAibqWG6kKb25-sx3F_myNxCcHEcv_v7pBPnFdwwtXiRrY8jPeUr-Aep6673EbCuDQ3I72_g0-s3t-LMG5xCbyi4IHBQP1hpl5ArmMU9XDGT-tJa8kYTvJGjFjEjY2G7CaKaHd6xi_mcT1Mt1OBPwFK4lyHKaeAh8Frm7TUK6pMJHP7etiCV_0udxJ9nH_61IskJIy-JwJyI4VRBGMz6Kydnn2tmCHfnjrUir9WAPPcNYwveF6o_I-No6RRm; FR24ID=5joaasp0e3f5hgs4m1ojm5d9udhhf7mkcqmhdel54m9e39jqqt9h; _frpk=NDevvDnVNEtR6nEwPWvaSA; hasConsentedToTerms=yes; __utmc=177865842; subscription=12; _frPl=NDevvDnVNEtR6nEwPWvaSNlcngfKdDRRHG9GXcAqvQE; __utma=177865842.2084412574.1552826958.1556628588.1556716510.4; __utmt=1; __utmb=177865842.7.10.1556716510; mac_overlay_count=450",
    'cache-control': "no-cache",
    'Postman-Token': "416ace9c-5ee3-4703-be5a-fd614537aa90"
}


class CommandLine:

    def __init__(self, db_username: str, db_passwd: str, api_key: str = None):
        engine, metadata = create_engine_and_metadata('10.0.1.4', db_username, db_passwd, 'flights')
        self.metadata = metadata
        self.route_db = RouteModel(engine, metadata, role='writer')
        self.airport_db = AirportsModel(engine, metadata, role='writer')
        self.miles_db = MilesModel(engine, metadata, role='writer')
        self.fr_route_db = FRRouteModel(engine, metadata, role='writer')
        self.api_key = api_key

    @staticmethod
    def rename_route(record: dict) -> dict:
        return dict(
            flight_number=int(record['flightNumber']),
            airline_iata=record['airlineIata'],
            airline_icao=record['airlineIcao'],
            departure_iata=record['departureIata'],
            departure_icao=record['departureIcao'],
            departure_terminal=record['departureTerminal'],
            departure_time=record['departureTime'],
            arrival_iata=record['arrivalIata'],
            arrival_icao=record['arrivalIcao'],
            arrival_terminal=record['arrivalTerminal'],
            arrival_time=record['arrivalTime'],
            reg_code=record['regNumber'])

    @staticmethod
    def rename_airport(record: dict) -> dict:
        return dict(
            id=int(record['airportId']),
            name=record['nameAirport'],
            iata_code=record['codeIataAirport'],
            icao_code=record['codeIcaoAirport'],
            translations_name=record['nameTranslations'],
            latitude=float(record['latitudeAirport']),
            longitude=float(record['longitudeAirport']),
            geo_name_id=record['geonameId'],
            timezone=record['timezone'],
            gmt=int(record['GMT']),
            country=record['nameCountry'],
            country_code_iso2=record['codeIso2Country'],
            city_iata_code=record['codeIataCity'])

    def download_airport_data_into_db(self, country_code: str):
        for airport in requests.get(url=' https://aviation-edge.com/v2/public/airportDatabase', params=dict(key=self.api_key, codeIso2Country=country_code)).json():
            try:
                self.airport_db.raw_insert(self.rename_airport(airport))
            except:
                print(airport)
                print(traceback.format_exc())

    def download_route_data_into_db(self, airline_iata: str):
        for route in requests.get(url=' http://aviation-edge.com/v2/public/routes', params=dict(key=self.api_key, airlineIata=airline_iata)).json():
            try:
                self.route_db.raw_insert(self.rename_route(route))
            except:
                print(route)
                print(traceback.format_exc())

    def download_fr24_route_data_into_local(self):
        for airport in self.airport_db.get_airport_by_country_code('JP'):
            route = requests.get(
                url='https://www.flightradar24.com/data/airlines/nu-jta/routes',
                headers=fr24_header,
                params={"get-airport-arr-dep": airport['iata_code']}).text
            try:
                with open('./datas/fr24/jta_{}.json'.format(airport['iata_code'].lower()), 'w') as writer:
                    # writer.write(json.dumps(route, ensure_ascii=False, sort_keys=True))
                    writer.write(route)
                    writer.write('\n')
            except:
                print(route)
                print(traceback.format_exc())
            time.sleep(1)

    def reload_fr24_jl_domestic_data_into_db(self):
        with open(os.path.abspath('./datas/fr24_jl_domestic_routes.json'), 'r') as reader:
            for line in reader.readlines():
                self.fr_route_db.raw_insert(json.loads(line))

    def reload_miles_data_into_db(self):
        with open(os.path.abspath('./datas/jmb_miles.json'), 'r') as reader:
            for line in reader.readlines():
                self.miles_db.raw_insert(json.loads(line))

    def reload_airport_data_into_db(self):
        with open(os.path.abspath('./datas/jp_airports.json'), 'r') as reader:
            for line in reader.readlines():
                self.airport_db.raw_insert(json.loads(line))

    def reload_all(self):
        self.metadata.drop_all()
        self.metadata.create_all()
        self.reload_airport_data_into_db()
        self.reload_fr24_jl_domestic_data_into_db()
        self.reload_miles_data_into_db()

    def export_db(self):
        with open('./datas/jmb_miles.json', 'w') as writer:
            for miles in self.miles_db.export_all():
                writer.write(json.dumps(miles, ensure_ascii=False, sort_keys=True))
                writer.write('\n')

        with open('./datas/jl_routes.json', 'w') as writer:
            for route in self.route_db.export_all():
                writer.write(json.dumps(route, ensure_ascii=False, sort_keys=True))
                writer.write('\n')

        with open('./datas/jp_airports.json', 'w') as writer:
            for airport in self.airport_db.export_all():
                airport['latitude'] = float(airport['latitude'])
                airport['longitude'] = float(airport['longitude'])
                writer.write(json.dumps(airport, ensure_ascii=False, sort_keys=True))
                writer.write('\n')


if __name__ == "__main__":
    Fire(CommandLine)
