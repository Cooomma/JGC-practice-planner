from datetime import datetime


def parse_time(time_str: str) -> datetime:
    return datetime.strptime(time_str, '%H:%M:%S')


def time_to_str(flight_time: datetime) -> str:
    return flight_time.strftime('%H:%M:%S')
