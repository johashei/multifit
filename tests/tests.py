from numba_stats import norm
import numpy as np
from numpy.random import default_rng
import sys
import unittest

#from UI import UI
#from generate_toy_data import ToySpectrum
sys.path.insert(0, "lib")
from rewrite import Spectrum, GaussianMaximumLikelyhood
from exceptions import *

class FittingTestCase(unittest.TestCase):
    def setUp(self):
        self.params = {'area':42.9182, 'mean':52.8375, 'stddev':1.7264}
        self.Fitter = GaussianMaximumLikelyhood(number_of_spectra=1, number_of_peaks=1)
        self.x = np.linspace(0, 100, 201)
        self.y = self.params['area']*norm.pdf(self.x, self.params['mean'], self.params['stddev'])

    def tearDown(self):
        pass

    def test_fit_result(self):
        self.Fitter.set_initial_values(self.params)
        self.Fitter.Fit(self.x, self.y) 
        fit_result = self.Fitter.get_result()
        failures = []
        for key, true_value in self.params.items():
            deviation_from_true_value =  abs(fit_result[key].value() - true_value)
            result_includes_true_value = deviation_from_true_value <= fit_result[key].stddev()
            if not result_includes_true_value:
                failures.append((key, true_value, fit_result[key].value()))
        self.assertEqual([], failures) 

    def test_fit_error(self):
        pass


class InputTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read_spectrum_file(self):
        pass


class SpectrumTestCase(unittest.TestCase):
    def setUp(self):
        rng = default_rng(seed=1337)
        self.random_counts1 = rng.integers(1, 10, 1e3)
        self.random_counts2 = rng.integers(1, 10, 5e2)

    def test_add_spectrum_with_subset_of_bins(self):
        spc1 = Spectrum(self.random_counts1)
        spc2 = Spectrum(self.random_counts2, start_channel=250, start_value=250*0.5)
        sum_of_counts = self.random_counts1
        sum_of_counts[250:750] += self.random_counts2
        expected_sum = Spectrum(sum_of_counts)
        obtained_sum = spc1 + spc2
        self.assertEqual(obtained_sum.counts, expected_sum.counts)
        self.assertEqual(obtained_sum.values, expected_sum.values)
        self.assertEqual(obtained_sum.channels, expected_sum.channels)
    
    def test_add_incompatible_spectrum(self):
        spc1 = Spectrum(self.random_counts1)
        spc2 = Spectrum(self.random_counts2, bin_width=1)
        expected_exception = BinningError
        self.assertRaises(expected_exception, spc1 + spc2)

    def test_add_offset_spectrum(self):
        pass


