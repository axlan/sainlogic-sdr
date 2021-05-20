#ifndef PPM_TRACKER_H
#define PPM_TRACKER_H

#include <Arduino.h>

#define MSG_LEN 128

// Class tracking pulse position modulated signal
class BinaryPpmTracker {
 public:
  BinaryPpmTracker(size_t min_samples, size_t max_samples) : min_samples_(min_samples), max_samples_(max_samples), last_sample_(false) {
    reset();
  }

  // Each sampled is passed in here
  // The processing is a state machine that looks for the sequences of
  // high to low, or low to high. The min and max sample parameters are
  // used to reject pulses that are not part of the actual message.
  void process_sample(bool sample) {
    if (cur_idx_ == MSG_LEN) {
      return;
    }
    if (sample != last_sample_) {
      if (repetitions_ > max_samples_ && repetitions_ < max_samples_ * 2) {
        if (edge_) {
          set_bit(!last_sample_);
          cur_idx_++;
        } else {
          reset();
        }
      }
      else if (repetitions_ > min_samples_) {
        if (!edge_) {
            set_bit(last_sample_);
            cur_idx_++;
        }
        edge_ = !edge_;
      } else {
        reset();
      }
      repetitions_ = 0;
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
  size_t cur_idx_;
  bool edge_;
  bool last_sample_;
  size_t repetitions_;
  uint8_t rx_data_[MSG_LEN/8];
};

#endif
