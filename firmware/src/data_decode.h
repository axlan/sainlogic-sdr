#ifndef DATA_DECODE_H
#define DATA_DECODE_H

#include <stdint.h>

bool check_crc(const uint8_t *msg);

// Get the wind direction in degrees
float get_direction(const uint8_t *msg);

// Get the temperature in degrees F
float get_temperature(const uint8_t *msg);

// Get average wind speed in m/s
float get_avr_wind_speed(const uint8_t *msg);

// Get gust wind speed in m/s
float get_gust_wind_speed(const uint8_t *msg);

// Get rain measurement in mm
float get_rain(const uint8_t *msg);

// Get humidity in %
float get_humidity(const uint8_t *msg);

#endif