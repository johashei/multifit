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
from functools import partial
from importlib import import_module
from itertools import groupby
import math
from typing import Iterable

from iminuit.util import describe
import numpy as np
import yaml


def bin_edges_iff_equal(spectra: Iterable):
    bin_edges = spectra[0].bin_edges
    for i, spectrum in enumerate(spectra[1:]):
        if (spectrum.bin_edges != bin_edges).any():
            raise ValueError(
                "Spectra must have equal bin edges. Inconsistent"
                f"bin edges were encountered in spectrum {i}.")
    return bin_edges

def all_equal(iterable: Iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def magnitude(value):
    if value == 0:
        return 0
    return int(round(math.log10(abs(value))))

def exponent(value):
    if value == 0:
        return 0
    return int(math.floor(math.log10(abs(value))))
