from dataclasses import dataclass
from iminuit import Minuit, cost
from iminuit.util import describe, make_func_code
import matplotlib.pyplot as plt
from numba_stats import norm
import numpy as np
import os
from pathlib import Path
import sys
import warnings


import exceptions
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
    def __init__(self, counts, xvals=None, start_value=0, bin_width=0.5, bins=None, start_bin=0):
        self.counts = np.asarray(counts)

        if bins is not None:
            check.same_length(counts, bins)
            self.bins = bins.astype(int)
        else:
            self.bins = np.arange(start_bin, start_bin+len(self.counts), 1).astype(int)
        
        if xvals is not None:
            check.same_length(counts, xvals[:-1])
            self.xvals = xvals
        else:
            self.xvals = np.arange(start_value, start_value+(len(self.counts) + 1)*bin_width, bin_width)

    def __call__(self, x):
        return self.counts[self.xval2bin(x)] 
        """
        access count by energy
        what energy inputs should be supported?
        
        # Handle both scalar and array-like argument
        x = np.asarray(x)
        scalar_input = False
        if x.ndim == 0:
            x = x[None]
            scalar_input = True
        """

    def __getitem__(self, bin):
        start = bin.start - self.bins[0]
        stop = bin.stop - self.bins[0]
        step = bin.step
        return self.counts[start:stop:step]


    def __add__(self, spectrum2):
        xvals_only_in_spectrum2 = np.setdiff1d(spectrum2.xvals, self.xvals)
        if xvals_only_in_spectrum2.size > 0:           
            message = f"trying to add counts to bins with xvals {xvals_only_in_spectrum2} which are not in self." #TODO: better error message
            raise exceptions.BinningError(message)
        print(len(spectrum2.xvals), len(spectrum2.bins))
        new_counts = self.counts
        for xval, bin in zip(spectrum2.xvals[:-1], spectrum2.bins):
            if self.get_bin_width(self.xval2bin(xval)) != spectrum2.get_bin_width(bin):
                message = f"bins starting at xval = {xval} do not have the same width"
                raise exceptions.BinningError(message)
            new_counts[self.xval2bin(xval)] += spectrum2(xval)
        return Spectrum(counts=new_counts, xvals=self.xvals, bins=self.bins)

    def get_bin_width(self, bin):
        bin_number = np.nonzero(self.bins == bin)[0]
        width = self.xvals[bin_number + 1] - self.xvals[bin_number]
        return width

    def xval2bin(self, xval):
        closest_bin = np.argmin(self.xvals - xval)
        if self.xvals[closest_bin] < xval:
            return closest_bin
        else:
            return closest_bin - 1 


    def get_calibration():
        # return a function to map the input xvals to the calibrated xvals.
        pass

    def scale(self, factor):
        self.counts *= factor



class Fitter:
    """
    Will not be interacted with directly by the user. Focus on expandablility over ease of input
    """
    independent_parameters = ['total_counts', 'slope', 'offset']
    shared_parameters = ['mean', 'stddev']


    def __init__(self, number_of_spectra, number_of_peaks):
        self.number_of_peaks = number_of_peaks
        self.number_of_spectra = number_of_spectra
        self.parameter_xvals = {}

    def set_background_model(self, model: callable, signature=None):
        if signature is not None:
            self.background = model
            self.background.func_code = make_func_code(signature)
        elif describe(model):
            self.background = model
        else:
            raise exceptions.MissingSignatureError(model)
        
    def def_peak_model(self, model: callable, signature=None):
        pass

    def set_resolution_curve(self, function: callable):
        pass

    def initialise_independent_parameters(self):
        for parameter in self.independent_parameters:
            pass
    
    def prepare_fit(self, counts, bin_edges):
        cost_function = cost.ExtendedBinnedNLL(counts, bin_edges, eval(self.lambda_string, globals(), locals()))
        self.minuit_object = Minuit(cost_function, **self.parameter_xvals)
    

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
