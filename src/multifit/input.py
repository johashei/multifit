"""Structure and loading of input files.
"""
from contextlib import chdir
from functools import partial
from importlib import import_module
from pathlib import Path
import sys
from typing import Iterable

from attrs import define, field
from iminuit.util import describe
import numpy as np
import yaml

from .data import Spectrum, CoincidenceMatrix

# Structure of the config file:

def _list_of(itemtype):
    def converter(iterable):
        return [itemtype(item) for item in iterable]
    return converter

def _dict_of(itemtype):
    def converter(d):
        return {key: itemtype(value) for key, value in d.items}
    return converter


@define
class DataConfig:
    directory: Path = field(converter=Path)
    files: list[Path] = field(converter=_list_of(Path))
    column: int
    delimiter: str
    bin_width: float


@define
class ModelConfig:
    module: Path = field(converter=Path)
    function: str
    number_of_peaks: int
    spectrum_params: list[str]
    peak_params: list[str]
    kwargs: dict


@define
class FitConfig:
    range: tuple = field(converter=tuple)
    mask: str  # this should probably be a different class
    parameter_ranges: dict[tuple] = field(converter=_dict_of(tuple))
    initial_values: dict[float]


@define
class Config:
    data: DataConfig
    model: ModelConfig
    fit: FitConfig

    @classmethod
    def from_yaml(cls, infile, raise_error=True):
        config = yaml.load(infile, yaml.CSafeLoader)
        try:
            data = DataConfig(**config['data'])
        except Exception as e:
            if raise_error:
                raise e
            else:
                print(
                    f"Warning: could not read data field. Error {e}",
                    file=sys.stderr
                    )
                data = None
        try:
            model = ModelConfig(**config['model']),
        except Exception as e:
            if raise_error:
                raise e
            else:
                print(
                    f"Warning: could not read model field. Error {e}",
                    file=sys.stderr
                    )
                model = None
        try:
            fit = FitConfig(**config['fit']),
        except Exception as e:
            if raise_error:
                raise e
            else:
                print(
                    f"Warning: could not read fit field. Error {e}",
                    file=sys.stderr
                    )
                fit = None
        return cls(data, model, fit)


def load_config(path_to_file, /, *, raise_error=True, check_completeness=True) -> Config:
    with open(path_to_file, 'r') as infile:
        config = Config.from_yaml(infile, raise_error=raise_error)
    if not check_completeness:
        return config
#   TODO: (Low priority) write full completeness check.
#    if (missing := (set(config) - required_keys)):
#        raise KeyError(f"The config file is missing the entries {missing}")
    if not (_remove_numbering(config.fit.parameter_ranges.keys())
            == _remove_numbering(config.fit.initial_values.keys())):
        raise KeyError("All fit parameters must have specified ranges "
                       "and initial values.")
    return config

def fetch_data(
        config: DataConfig,
        cls: Spectrum | CoincidenceMatrix,
        sorting_key=0,  # a constant keeps the ordering of the config file
        npy=True
    ) -> list[Spectrum | CoincidenceMatrix]:
    if callable(sorting_key):
        get_key = sorting_key
    else:
        def get_key(_):
            return sorting_key
    data = []
    for file in config.files:
        if npy:
            npfile = config.directory/file.with_suffix('.npy')
            try:
                counts = np.load(npfile)
            except FileNotFoundError:
                counts = np.loadtxt(
                    config.directory/file,
                    delimiter=config.delimiter,
                    usecols=config.column
                    )
                np.save(npfile, counts, allow_pickle=False)
        else:
            counts = np.loadtxt(
                config.directory/file,
                delimiter=config.delimiter,
                usecols=config.column
                )
        data.append(cls.equal_bins(
            counts=counts,
            bin_width=config.bin_width,
            key=get_key(file)
            ))
    data.sort()
    return data

def import_cdf(path: Path, function: str) -> callable:
    with chdir(path.parent):
        sys.path.insert(0, './')
        cdf_module = import_module(path.stem)
        sys.path.pop(0) # remove to avoid potential import problems later
    cdf = getattr(cdf_module, function)
    return cdf

def _remove_numbering(parameters: Iterable) -> set:
    """Return the parameters with peak and spectrum numbers removed."""
    return set([p.split('_')[0] for p in parameters])


