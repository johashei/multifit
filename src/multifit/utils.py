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


def approximate_pdf(cdf, dx) -> callable:
    def pdf(x, *args, **kwargs):
        return (cdf(x + dx/2, *args, **kwargs)
                - cdf(x - dx/2, *args, **kwargs)
                )/dx
    return pdf

def extract_parameters(log: dict, call: int, peak: int, spectrum: int) -> dict:
    try:
        return {
            key.split('_')[0]: float(value) for key, value # njit requires float
            in log[f'migrad_{call}']['minimum'].items()
            if key.split('_')[1] in (str(peak), '*')
                and key.split('_')[2] in (str(spectrum), '*')
            }
    except IndexError:
        # unique parameters formatted as x, not as x_*_*
        parameters = {}
        for key, value in log[f'migrad_{call}']['minimum'].items():
            splitkey = key.split('_')
            if len(splitkey) == 1:
                parameters[splitkey[0]] = float(value)
            elif (splitkey[1] in (str(peak), '*')
                  and splitkey[2] in (str(spectrum), '*')):
                parameters[splitkey[0]] = float(value)
        return parameters

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
