import os
from dotenv import find_dotenv, load_dotenv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

load_dotenv(find_dotenv())

user = os.getenv('USER')
password = os.getenv('PASSWORD')
host = os.getenv('HOST')  
port = os.getenv('PORT')      
database = os.getenv('DATABASE')

country_to_timezone = {
    "US" : "America/New_York",
    "JP" : "Asia/Tokyo",
    "DE" : "Europe/Berlin",
    "IT" : "Europe/Rome"
}


def get_time(timestamp, timezone):
        time = int(timestamp)
        utc_datetime = datetime.fromtimestamp(time)
        local_datetime = utc_datetime.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(timezone))
        return local_datetime

def get_delta_time(t1, t2):
    dt1 = datetime.fromtimestamp(t1)
    dt2 = datetime.fromtimestamp(t2)
    time_diff = abs(dt1 - dt2)

    return time_diff.days

def get_day_bounds(unix_timestamp):
    
    dt = datetime.fromtimestamp(unix_timestamp)
    start_of_day = datetime(dt.year, dt.month, dt.day)
    end_of_day = start_of_day + timedelta(hours=23, minutes=59, seconds=59)

    start_timestamp = int(start_of_day.timestamp())
    end_timestamp = int(end_of_day.timestamp())
    
    return start_timestamp, end_timestamp


def fix_day(day):
    date_specified = True
    if day is None:
         day = datetime.today()
         date_specified = False
    else:
        day = datetime.combine(day , datetime.min.time())
        day += timedelta(hours=23, minutes=59, seconds=59)
    return day, date_specified

def coalesce(num):
    if num is None:
        num = 0
    return num
    