"""
Based on https://support.weather.com/s/article/PWS-Upload-Protocol?language=en_US

NOT all fields need to be set, the _required_ elements are:
  ID
  PASSWORD 
  dateutc
IMPORTANT all fields must be url escaped
reference http://www.w3schools.com/tags/ref_urlencode.asp
example
  2001-01-01 10:32:35
   becomes
  2000-01-01+10%3A32%3A35
if the weather station is not capable of producing a timestamp, our system will accept "now". Example:
dateutc=now
list of fields:
action [action=updateraw] -- always supply this parameter to indicate you are making a weather observation upload
ID [ID as registered by wunderground.com]
PASSWORD [Station Key registered with this PWS ID, case sensitive]
dateutc - [YYYY-MM-DD HH:MM:SS (mysql format)] In Universal Coordinated Time (UTC) Not local time
winddir - [0-360 instantaneous wind direction]
windspeedmph - [mph instantaneous wind speed]
windgustmph - [mph current wind gust, using software specific time period]
windgustdir - [0-360 using software specific time period]
windspdmph_avg2m  - [mph 2 minute average wind speed mph]
winddir_avg2m - [0-360 2 minute average wind direction]
windgustmph_10m - [mph past 10 minutes wind gust mph ]
windgustdir_10m - [0-360 past 10 minutes wind gust direction]
humidity - [% outdoor humidity 0-100%]
dewptf- [F outdoor dewpoint F]
tempf - [F outdoor temperature]
* for extra outdoor sensors use temp2f, temp3f, and so on
rainin - [rain inches over the past hour)] -- the accumulated rainfall in the past 60 min
dailyrainin - [rain inches so far today in local time]
baromin - [barometric pressure inches]
weather - [text] -- metar style (+RA)
clouds - [text] -- SKC, FEW, SCT, BKN, OVC
soiltempf - [F soil temperature]
* for sensors 2,3,4 use soiltemp2f, soiltemp3f, and soiltemp4f
soilmoisture - [%]
* for sensors 2,3,4 use soilmoisture2, soilmoisture3, and soilmoisture4
leafwetness  - [%]
+ for sensor 2 use leafwetness2
solarradiation - [W/m^2]
UV - [index]
visibility - [nm visibility]
indoortempf - [F indoor temperature F]
indoorhumidity - [% indoor humidity 0-100]
Pollution Fields:
AqNO - [ NO (nitric oxide) ppb ]
AqNO2T - (nitrogen dioxide), true measure ppb
AqNO2 - NO2 computed, NOx-NO ppb
AqNO2Y - NO2 computed, NOy-NO ppb
AqNOX - NOx (nitrogen oxides) - ppb
AqNOY - NOy (total reactive nitrogen) - ppb
AqNO3 -NO3 ion (nitrate, not adjusted for ammonium ion) UG/M3
AqSO4 -SO4 ion (sulfate, not adjusted for ammonium ion) UG/M3
AqSO2 -(sulfur dioxide), conventional ppb
AqSO2T -trace levels ppb
AqCO -CO (carbon monoxide), conventional ppm
AqCOT -CO trace levels ppb
AqEC -EC (elemental carbon) – PM2.5 UG/M3
AqOC -OC (organic carbon, not adjusted for oxygen and hydrogen) – PM2.5 UG/M3
AqBC -BC (black carbon at 880 nm) UG/M3
AqUV-AETH  -UV-AETH (second channel of Aethalometer at 370 nm) UG/M3
AqPM2.5 - PM2.5 mass - UG/M3
AqPM10 - PM10 mass - PM10 mass
AqOZONE - Ozone - ppb
softwaretype - [text] ie: WeatherLink, VWS, WeatherDisplay

"""

from datetime import timezone
import datetime
import time

import requests
import pandas as pd

from .unit_conversions import millimeters_to_inches, meters_per_second_to_miles_per_hour, wind_dir_correction

class WUndergroundUploadAPI:
    """
    """
    _base_url = 'https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
    _rain_interval_sec = 60 * 60

    def __init__(self, station_id: str, station_key: str):
        """Creates a new WUndergroundUploadAPI object
        :param str station_id: [ID as registered by wunderground.com]
        :param str station_key: A[Station Key registered with this PWS ID, case sensitive]
        """
        self.station_key = station_key
        self.station_id = station_id
        self.rain_series = pd.Series(dtype='float64')
        self.last_rain = None

    def send_data(self, params):
        """Forward a raw request to Weather Underground API"""
        dt = datetime.datetime.now(timezone.utc)
        r = requests.get(self._base_url, params={
            'ID': self.station_id,
            'PASSWORD': self.station_key,
            'dateutc': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'updateraw',
            **params
        })
        r.raise_for_status()
        return r.text

    def __update_rain(self, measurement):
        if self.last_rain is None or measurement < self.last_rain:
            fell = 0
        else:
            fell = measurement - self.last_rain
        self.last_rain = measurement
        now = time.time()
        self.rain_series[now] = fell
        # drop old measurements
        old_idx =  self.rain_series[now - self.rain_series.index > WUndergroundUploadAPI._rain_interval_sec].index
        self.rain_series.drop(old_idx, inplace=True)
        return self.rain_series.sum()

    def send_sainlogic(self, values):
        """Forward Sainlogic data to Weather Underground API"""
        rainfall = self.__update_rain(values['rain'])

        params = {
            'rainin': millimeters_to_inches(rainfall),
            'humidity': values['humidity'],
            'winddir': wind_dir_correction(values['wind_dir']),
            'windgustmph': meters_per_second_to_miles_per_hour(values['gust_wind']),
            'windspeedmph': meters_per_second_to_miles_per_hour(values['avr_wind']),
            'tempf': values['temp']
        }
        return self.send_data(params)
