from typing import Iterable, Self
from iminuit import Minuit
from iminuit.cost import ExtendedBinnedNLL
from iminuit.util import describe, make_with_signature
import matplotlib.pyplot as plt
import numpy as np

from .data import Spectrum
from .plotter import IntervalSelectorGUI
from .model import Model
from .utils import bin_edges_iff_equal
from .interface import fetch_spectra


class Fitter:
    def __init__(
            self, *,
            spectra: Iterable[Spectrum],
            peak_model: Model,
            number_of_peaks: int):
        """Constructor for the Fitter class."""
        self.spectra = spectra
        self.bin_edges = bin_edges_iff_equal(spectra)
        self.peak_model = peak_model
        self.number_of_peaks = number_of_peaks
        self.loglikelihood = 0
        self.mask = None
        self._edge_range_values = (self.bin_edges[0], self.bin_edges[-1])
        self._parameter_values = {}
        self._parameter_limits = {}

    @classmethod
    def from_config(cls, config: dict) -> Self:
        spectra = fetch_spectra(config, 0)
        model = Model.from_config(config)
        instance = cls(
            spectra=spectra,
            peak_model=model,
            number_of_peaks=config['fit']['number_of_peaks'])
        instance.range = config['fit']['range']
        instance.parameter_values = config['fit']['initial_values']
        instance.parameter_limits = config['fit']['parameter_ranges']
        return instance

    @property
    def minuit(self):
        if not self.loglikelihood:
            self.make_cost_function()
#        for i, (key, value) in enumerate(self.loglikelihood._parameters.items()):
#            print(f'{i:2d} {key:12s}:{value}\t'
#                  f"{(self.parameter_values[key] if key in self.parameter_values else 'missing')}"
#                  )
        m = Minuit(self.loglikelihood, **self.parameter_values)
        for key, value in self.parameter_limits.items():
            m.limits[key] = value
        return m

    @property
    def range(self):
        return self._edge_range_values

    @range.setter
    def range(self, interval):
        """Set the range for the fit.

        The range is set such that all bins are fully included in the
        closed interval.
        """
        #lower_bin_edge, upper_bin_edge = interval
        lower_bin_edge = interval[0]
        upper_bin_edge = interval[-1] # allows for intermediate values used by the cdf
        idx_min = np.searchsorted(self.bin_edges, lower_bin_edge, 'left')
        idx_max = np.searchsorted(self.bin_edges, upper_bin_edge, 'right')
        self.edge_range_idx = np.s_[idx_min:idx_max]
        self.counts_range_idx = np.s_[idx_min:idx_max-1]
        self._edge_range_values = (self.bin_edges[idx_min],
                                   self.bin_edges[idx_max-1])

    @property
    def parameter_values(self) -> dict:
        return self._parameter_values

    @parameter_values.setter
    def parameter_values(self, values: dict):
        self._parameter_values = self._parse_parameter_values(values)

    @property
    def parameter_limits(self) -> dict:
        return self._parameter_limits

    @parameter_limits.setter
    def parameter_limits(self, limits: dict):
        self._parameter_limits = self._parse_parameter_values(limits)

    def _parse_parameter_values(self, arg: dict) -> dict:
        """Return parameter values following the notation scheme in Model."""
        values = {}
        for param, value in arg.items():
            values.update(dict.fromkeys(
                self.peak_model.match_param(
                    param,
                    spectrum_numbers=np.arange(len(self.spectra)),
                    peak_numbers=np.arange(self.number_of_peaks)
                    ),
                value
                ))
        return values

    def set_graphical_range(self):
        """Set the fitting range graphically."""
        selector = IntervalSelectorGUI(self.spectra)
        selector.run_widget()
        self.range = selector.interval

    def make_cost_function(self):
        """Combine the individual CDFs into a shared cost function."""
        for spectrum_number, spectrum in enumerate(self.spectra):
            component = ExtendedBinnedNLL(
                spectrum.counts[self.counts_range_idx],
                spectrum.bin_edges[self.edge_range_idx],
                self.sum_cdfs(spectrum_number)
                )
            if self.mask is not None:
                component.mask = self.mask[self.counts_range_idx]
            self.loglikelihood += component

    def sum_cdfs(self, spectrum_number) -> callable:
        signature = {}
        cdfs = [0]*self.number_of_peaks
        for peak_number, i in enumerate(range(self.number_of_peaks)):
            cdfs[i] = self.peak_model.make_cdf(
                peak_number=peak_number,
                spectrum_number=spectrum_number)
            signature |= cdfs[i]._parameters

#        for i, (key, value) in enumerate(signature.items()):
#            print(f"{i:2d}  {key:10s}: {value}")

        def sum_cdf(*args):
            # args must be positionsal, but I need the names for extraction
            parameters = {key: arg for key, arg in zip(signature, args)}
            result = 0
            for cdf in cdfs:
                cdf_args = [parameters[key] for key in cdf._parameters]
                result += cdf(*cdf_args)
#            result /= self.number_of_peaks  # normalize the cdf
            return result

        sum_cdf._parameters = signature
        return sum_cdf
