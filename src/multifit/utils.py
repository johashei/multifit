from functools import partial
from importlib import import_module
from itertools import groupby
import math
from typing import Iterable

from iminuit.util import describe
import numpy as np
import yaml

from .data import Spectrum
from .model import Model
from .interface import import_cdf



def bin_edges_iff_equal(spectra: Iterable[Spectrum]):
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
