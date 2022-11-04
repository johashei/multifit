from dataclasses import dataclass
from iminuit import Minuit, cost
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

    def get_calibration():
        # return a function to map the input values to the calibrated values.
        pass

    def scale(self, factor):
        self.counts *= factor


class GaussianMaximumLikelihood:
    """
    Will not be interacted with directly by the user. Focus on expandablility over ease of input
    """
    independent_parameters = ['total_counts', 'slope', 'offset']
    shared_parameters = ['mean', 'stddev']


    def __init__(self, number_of_spectra, number_of_peaks):
        self.number_of_peaks = number_of_peaks
        self.number_of_spectra = number_of_spectra
        self.parameter_values = {}

    def set_resolution_curve(self, function: callable):
        pass

    def make_fit_function(self):
        peak_args_string = "stddev_at_0, stddev_increase"
        for i in range(self.number_of_peaks):
            peak_args_string += ", total_counts_peak{i}, mean_peak{i}"
        background_args_string = "background_offset, background_slope"
        self.lambda_string = f"lambda x, {background_args_string}, {peak_args_string}: \
            _polynomial(x, {background_args_string}) + \
            _gaussian_cdf(x, {peak_args_string})"

    def initialise_independent_parameters(self):
        for parameter in self.independent_parameters:
            pass
    
    def prepare_fit(self, counts, bin_edges):
        cost_function = cost.ExtendedBinnedNLL(counts, bin_edges, eval(self.lambda_string, globals(), locals()))
        self.minuit_object = Minuit(cost_function, **self.parameter_values)
    

@dataclass
class Parameter:
    role: str
    peak: int
    spectrum: int

def _gaussian_cdf(x, *args):
    ret = np.zeros_like(x)
    for total_counts, mean in zip (args[2::2], args[3::2]):
        stddev = args[0] + args[1]*mean
        ret += total_counts*norm.cdf(x, mean, stddev)
    return ret

def _polynomial(x, *coefficients):
    return np.polynomial.polynomial.Polynomial(coefficients)(x)
