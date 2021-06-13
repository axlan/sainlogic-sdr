#ifndef PPM_TRACKER_H
#define PPM_TRACKER_H

#include <Arduino.h>

#define MSG_LEN 128
#define MSG_BYTES 16

// Class tracking pulse position modulated signal
class BinaryPpmTracker {
 public:

  /**
   * Initialize with parameters
   *
   * min_samples: The minimum number of sample of a high or low pulse to be
   *              considered part of a message
   * max_samples: 2 * max_samples is the maximum number of sample of a high or
   *              low pulse to be considered part of a message. For valid
   *              pulses > max_samples they're considered to be a bit value
   *              transition
   */
  BinaryPpmTracker(size_t min_samples, size_t max_samples) : min_samples_(min_samples), max_samples_(max_samples), last_sample_(false) {
    reset();
  }

  // Each sampled is passed in here
  // The processing is a state machine that looks for the sequences of
  // high to low, or low to high. The min and max sample parameters are
  // used to reject pulses that are not part of the actual message.
  void process_sample(bool sample) {
    // Once a message is received don't update until reset
    if (cur_idx_ == MSG_LEN) {
      return;
    }
    // When a zero crossing occurs
    if (sample != last_sample_) {
      // Reset the tracking
      bool lost = true;
      // A new bit is decoded
      bool found = false;
      // Only start the message on a high to low
      if ((cur_idx_ != 0 or last_sample_) and repetitions_ < max_samples_ and repetitions_ > min_samples_) {
        lost = false;
        if (!edge_) {
          found = true;
        }
        edge_ = !edge_;
      // Handle the case where a bit change causes a value to get held for two symbols
      } else if (repetitions_ > max_samples_ && repetitions_ < max_samples_ * 2) {
        if (edge_) {
          found = true;
        }
      }
      repetitions_ = 0;
      if (found) {
        // Handle glitch where first bit is sometimes missed
        if (cur_idx_ == 9 && sample) {
          set_bit(true);
          cur_idx_++;
        }
        set_bit(last_sample_);
        cur_idx_++;
      } else if (lost) {
        reset();
      }
    } else {
      repetitions_++;
    }
    last_sample_ = sample;
  }

  // Clear current state
  void reset() {
    cur_idx_ = 0;
    edge_ = 0;
    repetitions_ = 0;
  }

  // Number of bits received in current burst
  size_t cur_rx_len() const {
    return cur_idx_;
  }

  // Array of bits received in burst
  const uint8_t *get_msg() const {
    return rx_data_;
  }

 private:

  void set_bit(bool value) {
    int bit_idx = 7 - cur_idx_ % 8;
    int byte_idx = cur_idx_ / 8;
    bitWrite(rx_data_[byte_idx], bit_idx, value);
  }

  const size_t min_samples_;
  const size_t max_samples_;
  // The current bit in the message being received
  size_t cur_idx_;
  // Since bits are high-low or low-high, tracks whether in the first or second half
  bool edge_;
  bool last_sample_;
  // How long has the current bit value been held
  size_t repetitions_;
  uint8_t rx_data_[MSG_LEN/8];
};

#endif
