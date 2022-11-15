from numba_stats import norm
import numpy as np
from numpy.random import default_rng
import sys
import unittest
import pytest

#from UI import UI
#from generate_toy_data import ToySpectrum
sys.path.insert(0, "lib")
from rewrite import Spectrum, Fitter
import exceptions 

"""
class FittingTestCase(unittest.TestCase):
    def setUp(self):
        self.params = {'area':42.9182, 'mean':52.8375, 'stddev':1.7264}
        self.Fitter = GaussianMaximumLikelyhood(number_of_spectra=1, number_of_peaks=1)
        self.x = np.linspace(0, 100, 201)
        self.y = self.params['area']*0.5*norm.pdf(self.x, self.params['mean'], self.params['stddev'])

    def tearDown(self):
        pass

    def test_correct_lambda_string(self):
        expected_lambda_string = ""
        pass

    def test_fit_result(self):
        self.Fitter.set_initial_xvals(self.params)
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
"""
def test_pytest():
    print("this test was found")
    assert True

# this uses pytest
class TestSpectrum:
    @pytest.fixture(autouse=True)
    def random_data(self):
        rng = default_rng(seed=1337)
        self.random_counts1 = rng.integers(1, 10, 1000)
        self.random_counts2 = rng.integers(1, 10, 500)

    def test_add_spectrum_with_subset_of_bins(self):
        spc1 = Spectrum(self.random_counts1)
        spc2 = Spectrum(self.random_counts2, start_value=250*0.5)
        sum_of_counts = self.random_counts1
        sum_of_counts[250:750] += self.random_counts2
        expected_sum = Spectrum(sum_of_counts)
        obtained_sum = spc1 + spc2
        np.testing.assert_array_equal(obtained_sum.counts, expected_sum.counts)
        np.testing.assert_array_equal(obtained_sum.xvals, expected_sum.xvals)
        np.testing.assert_array_equal(obtained_sum.bins, expected_sum.bins)
    
    def test_add_incompatible_spectrum(self):
        spc1 = Spectrum(self.random_counts1)
        spc2 = Spectrum(self.random_counts2, bin_width=1)
        expected_exception = exceptions.BinningError
        with pytest.raises(expected_exception):
            spc1 + spc2

    def test_add_offset_spectrum(self):
        pass

    def test_getitem_range(self):
        spc = Spectrum(self.random_counts1, start_bin=42)
        gotten_item = spc[142:242:2]
        expected_item = self.random_counts1[100:200:2]
        np.testing.assert_array_equal(gotten_item, expected_item)

if __name__ == "__main__":
    retcode = pytest.main()
