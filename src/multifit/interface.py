from collections import defaultdict, OrderedDict
from functools import partial
from importlib import import_module
import json
from pathlib import Path
import sys
from typing import TextIO, Iterable

from iminuit import Minuit
from iminuit.util import describe
import numpy as np
import yaml

from .data import Spectrum, CoincidenceMatrix

def load_config(path_to_file, /, *, check_completeness=True) -> dict:
    with open(path_to_file, 'r') as infile:
        config = yaml.load(infile, yaml.CSafeLoader)

    if not check_completeness:
        return config

#   TODO: (Low priority) write full completeness check.
#    if (missing := (set(config) - required_keys)):
#        raise KeyError(f"The config file is missing the entries {missing}")
    if not (remove_numbering(config['fit']['parameter_ranges'].keys())
            == remove_numbering(config['fit']['initial_values'].keys())):
        raise KeyError("All fit parameters must have specified ranges "
                       "and initial values.")
    return config

def fetch_spectra(config: dict, key) -> list[Spectrum]:
    return fetch_data(config, key, cls=Spectrum)

def fetch_data(
        config: dict, key, cls: type, npy=True
    ) -> list[Spectrum | CoincidenceMatrix]:
    if callable(key):
        get_key = key
    else:
        def get_key(_):
            return key
    data = []
    for file in config['data']['files']:
        if npy:
            npfile = f"{config['data']['directory']}/{file.rsplit('.', 1)[0]}.npy"
            try:
                counts = np.load(npfile)
            except FileNotFoundError:
                counts = np.loadtxt(
                    f"{config['data']['directory']}/{file}",
                    delimiter=config['data']['delimiter'],
                    usecols=tuple(config['data']['column'])
                    )
                np.save(npfile, counts, allow_pickle=False)
        else:
            counts = np.loadtxt(
                f"{config['data']['directory']}/{file}",
                delimiter=config['data']['delimiter'],
                usecols=tuple(config['data']['column'])
                )
        data.append(cls.equal_bins(
            counts=counts,
            bin_width=config['data']['bin_width'],
            key=get_key(file)
            ))
    data.sort()
    return data

def import_cdf(config: dict) -> callable:
    path, _, name = config['model']['module'].rpartition('/')
    if path:
        sys.path.insert(0, path)
    else:
        sys.path.insert(0, './') # where the code is run
    cdf_module = import_module(name.rstrip('.py'))
    sys.path.pop(0) # remove to avoid potential import problems later

    original_cdf = getattr(cdf_module, config['model']['function'])

    cdf = prepare_cdf(
        original_cdf,
        config['fit']['range'],
        config['fit']['initial_values']
        )
    return cdf

def prepare_cdf(original_cdf, range, initial_values):
    parameter_order = describe(original_cdf)
    cdf = partial(original_cdf,
                  range=np.array(range, dtype=np.float64))
    cdf._parameters = {'x': None} | {
        par: None for par in parameter_order
        if par in remove_numbering(initial_values)
        }
    #cdf._parameters = {'x': (None, None)} | config['fit']['parameter_ranges']
    # limits now set in fitter.py to let a parameter have different limits
    # for different peaks peaks or spectra.
    return cdf

# ERROR: By using a set the order is garbled, causing iminuit to mix up
# the parameters. Preferably order should not be necessary in the config file.
def remove_numbering(parameters: Iterable) -> set:
    """Return the parameters with peak and spectrum numbers removed."""
    return set([p.split('_')[0] for p in parameters])
