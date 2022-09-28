from iminuit import Minuit
from iminuit.util import describe
import matplotlib.pyplot as plt
from numba_stats import norm
import numpy as np
import os
from pathlib import Path
import sys
import warnings


from exceptions import *
import check 

class UI:
    """
    initialize and call other classes in the correct order
    """

class IO:
    """
    read files and user input, generate output files and plots
    """
    def __init__(self):
        pass



class Spectrum:
    def __init__(self, counts, values=None, start_value=0, bin_width=0.5, channels=None, start_channel=0):
        self.counts = np.asarray(counts)

        if channels is not None:
            check.same_length(counts, channels)
            self.channels = channels.astype(int)
        else:
            self.channels = np.arange(start_channel, start_channel+len(self.counts), 1).astype(int)
        
        if values is not None:
            check.same_length(counts, values)
            self.values = values
        else:
            self.values = np.arange(start_value, start_value+len(self.counts)*bin_width, bin_width)

    def __call__(self, x):
        """
        access count by energy
        what energy inputs should be supported?
        """
        # Handle both scalar and array-like argument
        x = np.asarray(x)
        scalar_input = False
        if x.ndim == 0:
            x = x[None]
            scalar_input = True

    def __getitem__(self, bin):
        start = bin.start - self.channels[0]
        stop = bin.stop - self.channels[0]
        step = bin.step
        return self.counts[start:stop:step]


    def __add__(self, spectrum2):
        pass

    def scale(self, factor):
        self.counts *= factor

class GaussianMaximumLikelihood:
    def __init__(self, number_of_spectra, number_of_peaks):
        self.number_of_spectra = number_of_spectra
        self.number_of_peaks = number_of_peaks
    
    def make_gaussian_cdf(self):
        args = []
        peaks = []
        for i in range(self.number_of_peaks):
            args += [f'area_peak{i}', 'mean_peak{i}', 'stddev_peak{i}']
            peaks += ['area_peak{i}*norm.cdf(mean_peak{i}, stddev_peak{i})']
        cdf_string = f''
