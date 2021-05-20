#include "ring_buffer.h"

uint8_t samples[SAMPLE_LEN/8];
volatile size_t samples_head=0;
volatile uint8_t sample_pin=0;
size_t samples_tail=0;

void set_sample_pin(uint8_t pin) {
  sample_pin = pin;
}

void ICACHE_RAM_ATTR sample_input()
{
  #ifdef DEBUG_SAMPLER
  if (samples_head == SAMPLE_LEN - 1) {
    return;
  }
  #endif
  int bit_idx = samples_head % 8;
  int byte_idx = samples_head / 8;
  bitWrite(samples[byte_idx], bit_idx, digitalRead(sample_pin));
  samples_head = (samples_head + 1) % SAMPLE_LEN;
}

size_t num_samples() {
  size_t len;
  noInterrupts();
  if (samples_head >= samples_tail) {
    len = samples_head - samples_tail;
  } else {
    len = samples_head + SAMPLE_LEN - samples_tail;
  }
  interrupts();
  return len;
}

bool get_next_sample() {
  int bit_idx = samples_tail % 8;
  int byte_idx = samples_tail / 8;
  samples_tail = (samples_tail + 1) % SAMPLE_LEN;
  return bitRead(samples[byte_idx], bit_idx);
}

void reset_sampler() {
  noInterrupts();
  samples_head = 0;
  interrupts();
  samples_tail = 0;
}

const uint8_t *get_sample_buffer() {
  return samples;
}
