/**
 * Bit packed ring buffer for sampling digital value on a pin
 *
 * Does not handle overflow or underflow at all.
 *
 * Sampler is interrupt safe
 *
 * Defining DEBUG_SAMPLER stops the buffer from wrapping allowing for a
 * one shot sampling from a reset call.
 */


#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include <Arduino.h>

#define SAMPLE_LEN 10240

// The digital been to sample in the sample function
void set_sample_pin(uint8_t pin);

// Callback for ISR or polling to add samples to buffer
void ICACHE_RAM_ATTR sample_input();

// How many samples are in buffer
size_t num_samples();

// Pops the oldest bit off of the buffer
bool get_next_sample();

// Clears all data from buffer
void reset_sampler();

#ifdef DEBUG_SAMPLER
// Directly access buffer for reading out one shot capture
const uint8_t *get_sample_buffer();
#endif

#endif