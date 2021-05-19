#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2021 <+YOU OR YOUR COMPANY+>.
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

import numpy as np
import time
from gnuradio import gr
from crc_calc import crc8

APROX_SYMBOL_DURATION = 0.0004625
NUM_BITS = 128

class sainlogic_decode(gr.sync_block):
    """
    docstring for block sainlogic_decode
    """
    def __init__(self, fs,threshold):
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
        self.next_time = 0
        self.max = 0

    def work(self, input_items, output_items):
        in0 = input_items[0]

        self.buffer = np.append(self.buffer, in0 > self.threshold)

        self.max = max(np.max(in0), self.max)

        if time.time() > self.next_time:
            # print(self.max)
            # print(np.max(in0))
            # print(np.mean(in0))
            # print(np.min(in0))
            self.next_time = time.time() + 2.

        #print(np.max(in0))

        if len(self.bits) == 0:
            pulse_start = np.argmax(self.buffer)
            if pulse_start == 0 and not self.buffer[0]:
                self.buffer = np.array([], dtype=bool)
                return len(in0)
            self.buffer = self.buffer[pulse_start:]
            self.bits.append(True)

        while len(self.bits) < NUM_BITS:
            if len(self.buffer) < self.pulse_check_len:
                return len(in0)
            neg_index = np.argmax(self.buffer != self.bits[-1])
            if neg_index == 0 or neg_index > self.pulse_offset_len:
                print('Bit not terminated')
                self.__reset()
                return len(in0)

            next_idx = neg_index + self.pulse_offset_len
            if len(self.bits) == 9 and not self.buffer[next_idx]:
                self.bits = [True] + self.bits
            self.bits.append(self.buffer[next_idx])
            self.buffer = self.buffer[next_idx:]

        self.__process_msg()
        self.__reset()
        return len(in0)

    def __reset(self):
        self.bits = []
        self.buffer = np.array([], dtype=bool)

    @staticmethod
    #deg
    def get_direction(bytes_vals):
        dir = bytes_vals[6]
        if bytes_vals[3] & 0b100:
            dir += 256
        return dir

    @staticmethod
    #F
    def get_temperature(bytes_vals):
        return (bytes_vals[9] * 256 + bytes_vals[10] - 33168 ) / 10.

    WIND_CONV_FACTOR = 0.224

    @staticmethod
    #MPH
    def get_avr_wind(bytes_vals):
        return bytes_vals[4] * 0.224

    @staticmethod
    #MPH
    def get_gust_wind(bytes_vals):
        return bytes_vals[5] * 0.224

    @staticmethod
    #inch
    def rain_measure(bytes_vals):
        return ( bytes_vals[7] * 256+bytes_vals[8]) * 0.0039336492890995264




    def __process_msg(self):
        bytes_vals = []
        for i in range(0, NUM_BITS, 8):
            bit_strs = [ '1' if x else '0' for x in self.bits[i:i+8] ]
            bit_str = ''.join(bit_strs)
            bytes_vals.append(int(''.join(bit_strs), 2))

        print(bytes_vals)
        if crc8(bytes_vals[:-1]) == bytes_vals[-1]:
            print({'temp': sainlogic_decode.get_temperature(bytes_vals),
                   'humidity': bytes_vals[11],
                   'wind_dir': sainlogic_decode.get_direction(bytes_vals),
                   'avr_wind': sainlogic_decode.get_avr_wind(bytes_vals),
                   'gust_wind': sainlogic_decode.get_gust_wind(bytes_vals) })
        else:
            print('CRC Failure')
