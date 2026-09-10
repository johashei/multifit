"""multifit: simultaneous fitting to multiple data sets.

Copyright (C) 2026 Johannes Sørby Heines

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Iterable, Self

from attrs import define
from iminuit import Minuit
from iminuit.cost import ExtendedBinnedNLL
from iminuit.util import describe, make_with_signature
import matplotlib.pyplot as plt
import numpy as np

from .data import Spectrum
from .model import Model
from .utils import bin_edges_iff_equal
from .input import FitConfig


class Fitter:
    def __init__(
            self, *,
            spectra: Iterable[Spectrum],
            peak_model: Model,
            ):
        """Constructor for the Fitter class."""
        self.spectra = spectra
        self.bin_edges = bin_edges_iff_equal(spectra)
        self.peak_model = peak_model
        self.loglikelihood = 0
        self.mask = None
        self._edge_range_values = (self.bin_edges[0], self.bin_edges[-1])
        self._parameter_values = {}
        self._parameter_limits = {}

    @classmethod
    def from_config(
            cls,
            spectra: Iterable[Spectrum],
            model: Model,
            config: FitConfig
            ) -> Self:
        instance = cls(spectra=spectra, peak_model=model)
        instance.range = config.range
        instance.parameter_values = config.initial_values
        instance.parameter_limits = config.parameter_ranges
        instance.mask = mask_from_ranges(config.mask, instance.bin_edges)
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
        upper_bin_edge = interval[-1]
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
                    peak_numbers=np.arange(self.peak_model.number_of_peaks)
                    ),
                value
                ))
        return values

    def make_cost_function(self):
        """Combine the individual CDFs into a shared cost function."""
        for spectrum_number, spectrum in enumerate(self.spectra):
            component = ExtendedBinnedNLL(
                spectrum.counts[self.counts_range_idx],
                spectrum.bin_edges[self.edge_range_idx],
                self.peak_model.sum_cdfs(spectrum_number)
                )
            if self.mask is not None:
                component.mask = self.mask[self.counts_range_idx]
            self.loglikelihood += component


def mask_from_ranges(ranges, bin_edges):
    mask = np.zeros_like(bin_edges)
    for [lower, upper] in ranges:
        mask |= (lower <= bin_edges) & (bin_edges < upper)
    return mask[:-1]  # remove the last element to index bins not edges
