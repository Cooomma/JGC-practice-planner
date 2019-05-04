from datetime import datetime


def parse_time(time_str: str) -> datetime:
    return datetime.strptime(time_str, '%H:%M:%S')


def time_to_str(flight_time: datetime) -> str:
    return flight_time.strftime('%H:%M:%S')


def transit_time(pervious_arrival_time: datetime, next_departure_time: datetime) -> datetime:
    return pervious_arrival_time - next_departure_time


def flight_duration(arrival_time: datetime, departure_time: datetime) -> datetime:
    return departure_time - arrival_time


def is_last_flight(arrivial_time: datetime) -> bool:
    return arrivial_time < parse_time('22:00:00')


def is_enough_to_transit(pervious_arrival_time: datetime, next_departure_time: datetime, transit_tolerance: int = 1800):
    return transit_time(pervious_arrival_time, next_departure_time).second() >= transit_tolerance


def is_not_over_night(previous_arrival_time: datetime, next_departure_time: datetime,) -> datetime:
    return previous_arrival_time > next_departure_time
