#!/usr/bin/env python2.7

# Author : Minjun J. Choi (mjchoi@nfri.re.kr)
#
# Description : Filter data 
#
# Acknowledgement : TomRoelandts.com
#
# Last updated
#  2018.12.15 : version 0.10;

import numpy as np
import h5py

class FiltData(object):
    def __init__(self, name, fs, fL, fH, b=0.08):
        self.name = name
        self.fs = fs
        self.fL = fL
        self.fH = fH
        self.b = b

        N = int(np.ceil((4 / b)))
        if not N % 2: N += 1

        self.coef = np.ones(N)

        if name == 'FIR_pass' and fL == 0:
            self.coef = self.fir_lowpass(float(fH/fs), N) 
        elif name == 'FIR_pass' and fH == 0:
            self.coef = self.fir_highpass(float(fH/fs), N)
#        elif name == 'FIR_pass' and fL != 0 and fH != 0:
#            self.coef = self.fir_bandpass(fL/fs, fH/fs, N)
        elif name == 'FIR_block':
            self.coef = self.fir_bandblock(fL/fs, fH/fs, N)

    def fir_lowpass(self, fc, N):
        n = np.arange(N)

        # Compute sinc filter.
        h = np.sinc(2 * fc * (n - (N - 1) / 2.))
        # Compute Blackman window.
        w = np.blackman(N)
        # Multiply sinc filter with window.
        h = h * w
        # Normalize to get unity gain.
        h = h / np.sum(h)

        return h

#    def fir_bandpass(self, fL, fH, N):  # do not use due to delay
#        n = np.arange(N)

#        # Compute a low-pass filter with cutoff frequency fH.
#        hlpf = np.sinc(2 * fH * (n - (N - 1) / 2.))
#        hlpf *= np.blackman(N)
#        hlpf = hlpf / np.sum(hlpf)
#        # Compute a high-pass filter with cutoff frequency fL.
#        hhpf = np.sinc(2 * fL * (n - (N - 1) / 2.))
#        hhpf *= np.blackman(N)
#        hhpf = hhpf / np.sum(hhpf)
#        hhpf = -hhpf
#        hhpf[(N - 1) / 2] += 1
#        # Convolve both filters.
#        h = np.convolve(hlpf, hhpf)

#        return h

    def fir_bandblock(self, fL, fH, N):
        n = np.arange(N)

        # Compute a low-pass filter with cutoff frequency fL.
        hlpf = np.sinc(2 * fL * (n - (N - 1) / 2.))
        hlpf *= np.blackman(N)
        hlpf /= np.sum(hlpf)
        # Compute a high-pass filter with cutoff frequency fH.
        hhpf = np.sinc(2 * fH * (n - (N - 1) / 2.))
        hhpf *= np.blackman(N)
        hhpf /= np.sum(hhpf)
        hhpf = -hhpf
        hhpf[(N - 1) / 2] += 1
        # Add both filters.
        h = hlpf + hhpf

        return h