"""Structure and loading of input files.
"""
from contextlib import chdir
from functools import partial
from pathlib import Path
from runpy import run_path
import sys
from typing import Iterable, TextIO
import warnings

from attrs import define, field
from iminuit.util import describe
import numpy as np
import yaml

from .data import Spectrum, CoincidenceMatrix

# type converters

def _list_of(itemtype):
    def converter(iterable):
        return [itemtype(item) for item in iterable]
    return converter

def _dict_of(itemtype):
    def converter(d):
        return {key: itemtype(value) for key, value in d.items()}
    return converter

# Structure of the config file:

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
#    mask: str  # TODO: find a better way to implement this functionality
    parameter_ranges: dict[tuple] = field(converter=_dict_of(tuple))
    initial_values: dict[float]

class IncompleteConfigWarning(Warning):
    pass

@define
class Config:
    data: DataConfig
    model: ModelConfig
    fit: FitConfig

    @classmethod
    def from_yaml(cls, file: TextIO | Path | str, error_if_incomplete=True):
        if isinstance(file, TextIO):
            config = yaml.load(file, yaml.CSafeLoader)
        else:
            with open(file, 'r') as infile:
                config = yaml.load(infile, yaml.CSafeLoader)
        fields = {'data': DataConfig, 'model': ModelConfig, 'fit': FitConfig}
        for key, typ in fields.items():
            try:
                fields[key] = typ(**config[key])
            except Exception as e:
                if error_if_incomplete:
                    raise e
                else:
                    warnings.warn(
                        f"Could not read {key} field. Error\n{e}",
                        category=IncompleteConfigWarning,
                        stacklevel=2
                        )
                fields[key] = None

        return cls(**fields)


def load_config(path_to_file, /, *, error_if_incomplete=True) -> Config:
    with open(path_to_file, 'r') as infile:
        config = Config.from_yaml(infile, raise_error=error_if_incomplete)
    return config

def check_completeness(config: Config):
#   TODO: (Low priority) write full completeness check.
#    if (missing := (set(config) - required_keys)):
#        raise KeyError(f"The config file is missing the entries {missing}")
    if not (_remove_numbering(config.fit.parameter_ranges.keys())
            == _remove_numbering(config.fit.initial_values.keys())):
        raise KeyError("All fit parameters must have specified ranges "
                       "and initial values.")

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
    path = path.resolve()
    # chdir in case the module uses relative imports
    with chdir(path.parent):
        cdf_module_dict = run_path(path)
    cdf = cdf_module_dict[function]
    return cdf

def _remove_numbering(parameters: Iterable) -> set:
    """Return the parameters with peak and spectrum numbers removed."""
    return set([p.split('_')[0] for p in parameters])


