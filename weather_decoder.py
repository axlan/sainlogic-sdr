import numpy as np
from crc_calc import crc8

APROX_SYMBOL_DURATION = 0.0004625
NUM_BITS = 128

class WeatherDecoder:

    def __init__(self, fs, threshold):
        # Need at least 4 samples per bit
        assert(fs > 1./APROX_SYMBOL_DURATION*2)
        self.fs = fs
        self.threshold = threshold
        self.aprox_symbol_samples = int(APROX_SYMBOL_DURATION * fs)
        # make sure to read a whole bit ahead to clear end of last symbol
        self.pulse_check_len = int(self.aprox_symbol_samples * 4.5)
        self.pulse_offset_len = int(self.aprox_symbol_samples * 1.5)
        self.buffer = np.array([], dtype=bool)
        self.bits = []


    def work(self, input_items, output_items=None):

        self.buffer = np.append(self.buffer, input_items > self.threshold)

        if len(self.bits) == 0:
            pulse_start = np.argmax(self.buffer)
            if pulse_start == 0 and not self.buffer[0]:
                self.buffer = np.array([], dtype=bool)
                return
            self.buffer = self.buffer[pulse_start:]
            self.bits.append(True)

        while len(self.bits) < NUM_BITS:
            if len(self.buffer) < self.pulse_check_len:
                return
            neg_index = np.argmax(self.buffer != self.bits[-1])
            assert(neg_index != 0)
            assert(neg_index < self.pulse_offset_len)

            next_idx = neg_index + self.pulse_offset_len
            if len(self.bits) == 9 and not self.buffer[next_idx]:
                self.bits = [True] + self.bits
            self.bits.append(self.buffer[next_idx])
            self.buffer = self.buffer[next_idx:]

        self.process_msg()
        self.bits = []
        self.buffer = np.array([], dtype=bool)


    def process_msg(self):
        bytes_vals = []
        for i in range(0, NUM_BITS, 8):
            bit_strs = [ '1' if x else '0' for x in self.bits[i:i+8] ]
            bit_str = ''.join(bit_strs)
            bytes_vals.append(int(''.join(bit_strs), 2))

        print(bytes_vals)
        assert(crc8(bytes_vals[:-1]) == bytes_vals[-1])
        print({'humidity': bytes_vals[11], 'wind_dir': bytes_vals[6], })


def test():
    dir = '/home/axlan/data/'
    
    # fs = 3.2e6
    # threshold = .015
    # filename = 'gqrx_20210508_054747_433900000_3200000_fc.raw'

    fs = 1.05e6
    threshold = .2
    filename = 'n1.raw'

    decoder = WeatherDecoder(fs, threshold)

    data = np.fromfile(dir + filename, dtype=np.csingle)
    mag_data = np.abs(data)

    BURST_SIZE = 100

    for i in range(0, len(mag_data), BURST_SIZE):
        decoder.work(mag_data[i:i+BURST_SIZE])


if __name__ == '__main__':
    test()
