#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include <Arduino.h>

#define SAMPLE_LEN 10240

void set_sample_pin(uint8_t pin);

void ICACHE_RAM_ATTR sample_input();

size_t num_samples();

bool get_next_sample();

void reset_sampler();

void start_sample_capture();

const uint8_t *get_sample_buffer();

#endif