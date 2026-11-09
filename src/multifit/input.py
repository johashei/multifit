"""multifit: simultaneous fitting to multiple data sets.
Module 'input': Structure and loading of input files.


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

# Ordering for documentation
__all__ = ['Config', 'DataConfig', 'ModelConfig', 'FitConfig', 'fetch_data', 'import_cdf']

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
    """Class for configuration of the input data.

    Data should be in the form of histograms with equal width bins.

    Attributes
    ----------
    directory: Path
        Directory from which to read the data files.
    files: list[Path]
        List of data files relative to `directory`
    bin_width: float
        Bin width of the data histograms.
    column: int
        Column of the data file containing the histogram content.
    delimiter:
        Column delimiter for data stored in a text file.
    """
    directory: Path = field(converter=Path)
    files: list[Path] = field(converter=_list_of(Path))
    bin_width: float
    column: int = 0
    delimiter: str = None


@define
class ModelConfig:
    """Class for configuration of the model

    The model consists of a cumulative density function describing a
    single peak structure. The function may be repeated to model several
    peak structures. Each function parameter may be shared by all peaks
    in a spectrum or all instances of a peak across spectra.

    Attributes
    ----------
    module: Path
        Path to the python module where the model function is defined.
    function: str
        Name of the function defining the model.
    number_of_peaks: int
        Number of peak structures to model for each spectrum.
    spectrum_params: list[str]
        Name of parameters to be shared by all peaks in a spectrum.
    peak_params: list[str]
        Name of parameters to be shared by all instances of the same
        peak across spectra.
    kwargs: dict
        Additional keyword arguments required by the function.
    """
    module: Path = field(converter=Path)
    function: str
    number_of_peaks: int
    spectrum_params: list[str]
    peak_params: list[str]
    kwargs: dict


@define
class FitConfig:
    """Class for configuration of the fit.

    Attributes
    ----------
    range: tuple | list[tuple]
        Range of data to fit. A single tuple is read as a range.
        A list of tuples is read as a union of ranges.
    parameter_ranges: dict[tuple]
        Allowed range for each fit parameter.
    initial_values:
        Initial values for each fit parameter.
    """
    range: tuple | list[tuple]
    parameter_ranges: dict[tuple] = field(converter=_dict_of(tuple))
    initial_values: dict[float]

class IncompleteConfigWarning(Warning):
    """Warning raised when values are missing from a configuration object."""
    pass

@define
class Config:
    """Class holding the full multifit configuration.

    See attribute classes for more detail.

    Attributes
    ----------
    data: DataConfig
        Configuration for reading the data.
    model: ModelConfig
        Configuration of the model.
    fit: FitConfig
        Configuration of the fit.
    """
    data: DataConfig
    model: ModelConfig
    fit: FitConfig

    @classmethod
    def from_yaml(cls, file: TextIO | Path | str, error_if_incomplete=True):
        """Initialize configuration from yaml configuration file.

        Arguments
        ---------
        file: TextIO | Path | str
            Configuration file to read.
        error_if_incomplete: bool
            If true, raise an error when the configuration file is
            incomplete. If false, issue a warning. (default True)
        """
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
    # Depracated, use Config.from_yaml instead
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
        cls,
        sorting_key=0,  # a constant keeps the ordering of the config file
        npy=True
    ) -> list[Spectrum | CoincidenceMatrix]:
    """Read data files.

    WARNING: This function will be depracated in the future.

    Arguments
    ---------
    config: DataConfig
        Data configuration object.
    cls
        Class to read the data into, possible values are `Spectrum` and
        `CoincidenceMatrix`.
    sorting_key
        key to use when sorting the data object list. May be a constant
        or a callable taking the file name as a positional argument.
    npy: bool
        If true, try to read the data from a .npy file. If such a file
        doesn't exist, generate it. (default True)

    Returns
    -------
    list[Spectrum | CoincidenceMatrix]
        Sorted list of data objects read from each file.
    """
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
    """Import a function from an arbitrary module.

    Arguments
    ---------
    path: Path
        Path to the python module containing the function.
    function: str
        Name of the function to import.

    Returns
    -------
    callable
        The imported function.
    """
    path = path.resolve()
    # chdir in case the module uses relative imports
    with chdir(path.parent):
        cdf_module_dict = run_path(path)
    cdf = cdf_module_dict[function]
    return cdf

def _remove_numbering(parameters: Iterable) -> set:
    """Return the parameters with peak and spectrum numbers removed."""
    return set([p.split('_')[0] for p in parameters])
