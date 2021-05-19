#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 axlan.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
import time

import numpy as np
from gnuradio import gr

from sainlogic.sainlogic_parser import get_measurements

APROX_SYMBOL_DURATION = 0.0004625
NUM_BITS = 128

class sainlogic_decode(gr.sync_block):
    """
    This block takes in the RF data, and tries to decode bits sent
    by the sainlogic sensor.

    Print decoded bytes and measurement.

    fs: the sampling rate
    threshold: the threshold for a sample to be be considered "high"
    """
    def __init__(self, fs, threshold):
        gr.sync_block.__init__(self,
            name="sainlogic_decode",
            in_sig=[np.float32],
            out_sig=None)
        # Need at least 4 samples per bit
        assert fs > 1./APROX_SYMBOL_DURATION*2
        self.fs = fs
        self.threshold = threshold
        self.aprox_symbol_samples = int(APROX_SYMBOL_DURATION * fs)
        # make sure to read a whole bit ahead to clear end of last symbol
        self.pulse_check_len = int(self.aprox_symbol_samples * 4.5)
        self.pulse_offset_len = int(self.aprox_symbol_samples * 1.5)
        self.buffer = np.array([], dtype=bool)
        self.bits = []
        self.max = 0

    def work(self, input_items, output_items):
        in0 = input_items[0]

        # Buffer whether the samples are above the threshold
        self.buffer = np.append(self.buffer, in0 > self.threshold)

        self.max = max(np.max(in0), self.max)

        # Detect possible start of message
        if len(self.bits) == 0:
            pulse_start = np.argmax(self.buffer)
            if pulse_start == 0 and not self.buffer[0]:
                self.buffer = np.array([], dtype=bool)
                return len(in0)
            self.buffer = self.buffer[pulse_start:]
            self.bits.append(True)

        # While in the middle of a message
        while len(self.bits) < NUM_BITS:
            # Only check for bits when there's enough buffered data
            if len(self.buffer) < self.pulse_check_len:
                return len(in0)
            # Synchronize on zero crossing in middle of bit
            neg_index = np.argmax(self.buffer != self.bits[-1])
            # If zero crossing isn't found, message decoding fails
            if neg_index == 0 or neg_index > self.pulse_offset_len:
                print('Bit not terminated')
                self.__reset()
                return len(in0)
            # Move on to next bit
            next_idx = neg_index + self.pulse_offset_len
            next_bit = self.buffer[next_idx]
            # Sometimes transmission misses the first bit
            # If preamble is too short append a bit to start
            if len(self.bits) == 9 and not next_bit:
                self.bits = [True] + self.bits
            self.bits.append(next_bit)
            # Remove processed buffer
            self.buffer = self.buffer[next_idx:]

        self.__process_msg()
        self.__reset()
        return len(in0)

    # Reset state to start looking for new message
    def __reset(self):
        self.bits = []
        self.buffer = np.array([], dtype=bool)

    # Print decoded bytes and measurement.
    def __process_msg(self):
        bytes_vals = []
        for i in range(0, NUM_BITS, 8):
            bit_strs = [ '1' if x else '0' for x in self.bits[i:i+8] ]
            bit_str = ''.join(bit_strs)
            bytes_vals.append(int(''.join(bit_strs), 2))

        print(bytes_vals)
        measurements = get_measurements(bytes_vals)
        if measurements is not None:
            print(measurements)
        else:
            print(f'CRC Failure')


    