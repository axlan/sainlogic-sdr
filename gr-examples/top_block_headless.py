#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Top Block
# Generated: Thu May 13 00:09:51 2021
##################################################

from distutils.version import StrictVersion

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import osmosdr
import sainlogic
import sys
import time


class top_block(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Top Block")

        ##################################################
        # Variables
        ##################################################
        self.fs = fs = 1e6
        self.fc = fc = 433.92e6
        self.threshold = threshold = .01

        ##################################################
        # Blocks
        ##################################################
        self.sainlogic_sainlogic_decode_0 = sainlogic.sainlogic_decode(fs, threshold)
        self.rtlsdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + '' )
        self.rtlsdr_source_0.set_sample_rate(fs)
        self.rtlsdr_source_0.set_center_freq(fc, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(10, 0)
        self.rtlsdr_source_0.set_if_gain(20, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna('', 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)

        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.sainlogic_sainlogic_decode_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.blocks_complex_to_mag_squared_0, 0))

    def get_fs(self):
        return self.fs

    def set_fs(self, fs):
        self.fs = fs
        self.rtlsdr_source_0.set_sample_rate(self.fs)

def main(top_block_cls=top_block, options=None):

    tb = top_block_cls()
    tb.start()
    print('started')
    try:
        time.sleep(600)
    except:
        pass
    print('stopping')
    tb.stop()
    print('stopped')
    tb.wait()
    print('done')


if __name__ == '__main__':
    main()
