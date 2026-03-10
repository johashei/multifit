""" Handle logging of the fit process done by iminuit.
"""

from collections import defaultdict
import json
from pathlib import Path
from typing import TextIO
import sys

from attrs import define
from iminuit import Minuit

class LoggedMinuit:
    """A wrapper around the Minuit class that writes logs to a json file.

    Public variables:
    json_settings: dict -- keyword arguments to pass to json.dumps when
        writing the logs.

    While the logs are human readable, it is usually easier to extract
    and visualise the relevant data.
    """

    __slots__ = (
        '_m',
        '_logfile',
        '_counter',
        'json_settings'
        )

    def __init__(self, m: Minuit, logfile: TextIO):
        """Constructor for the LoggedMinuit wrapper class.

        Arguments:
        m -- the Minuit object to wrap.
        logfile -- the file object to which the log will be written.
        """
        self._m = m
        self._logfile = logfile
        self._counter = defaultdict(int)
        self.json_settings = {
            'indent': '\t',
            'ensure_ascii': False
            }
        if self._logfile.mode in ['w', 'x', 'w+']: # Empty file
            self.update_infoline()
            self._logfile.write('}\n') # Close json dict

    def __getattr__(self, attr):
        return getattr(self._m, attr)

    def __setattr__(self, attr, value):
        try:
            object.__setattr__(self, attr, value)
        except AttributeError as e_self:  # This works because __slots__
            setattr(self._m, attr, value)

    def migrad(self, *args, **kwargs):
        result = self._m.migrad(*args, **kwargs)
        self._counter['migrad'] += 1
        log = {f"migrad_{self._counter['migrad']}": {
            'args': args,
            'kwargs' : kwargs,
            'algorithm': self._m.fmin.algorithm,
            'strategy': self._m.strategy.strategy,
            'valid_minimum': self._m.valid,
            'parameters_at_limit': self._m.fmin.has_parameters_at_limit,
            'reduced_chi2': self._m.fmin.reduced_chi2,
#            'mask': self._m.fcn._fcn.mask,
            'fixed': self.fixed,
            'limits': self._m.limits.to_dict(),
            'minimum': {key: value for key, value in
                        zip(self._m.parameters, self._m.values)},
            }
        }
        self.append_to_log(log)
        return result

    def hesse(self, *args, **kwargs):
        result = self._m.hesse(*args, **kwargs)
        self._counter['hesse'] += 1
        log = {
                (key := f"hesse_{self._counter['hesse']}"): {
                'args': args,
                'kwargs': kwargs,
                'valid_minimum': self._m.valid,
                'hesse_succeeded': not self._m.fmin.hesse_failed,
                'accurate_covar': self._m.fmin.has_accurate_covar,
                'parameters_at_limit': self._m.fmin.has_parameters_at_limit,
                'fixed': self.fixed,
                'limits': self._m.limits.to_dict(),
                'errors': {key: error for key, error in
                           zip(self._m.parameters, self._m.errors)},
                }
            }
        subkey = 'covariance, correlation'
        try:
            correlation = self._m.covariance.correlation() # compute once
            # json cant use tuples as key, so make strings instead
            log[key][subkey] = {
                f'({key[0]}, {key[1]})': [cov, correlation[key]] for key, cov in
                self._m.covariance.to_dict().items()
                }
        except AttributeError:
            # Covariance could not be calculated thus is None
            print("WARNING: Covariance could not be calculated.\n",
                  file=sys.stderr
                  )
            log[key][subkey] = {}
        self.append_to_log(log)
        return result

    def minos(self, *args, **kwargs):
        result = self._m.minos(*args, **kwargs)
        self._counter['minos'] += 1
        log = {f"minos_{self._counter['minos']}": {
            'args': args,
            'kwargs': kwargs,
            'valid_minimum': self._m.valid,
            'merror_failed': [key for key, merror in self._m.merrors.items()
                             if not merror.is_valid],
            'lower_new_min': {key: merror.lower_new_min for key, merror in
                              self._m.merrors.items() if merror.lower_new_min},
            'upper_new_min': {key: merror.upper_new_min for key, merror in
                              self._m.merrors.items() if merror.upper_new_min},
            'at_lower_limit': [key for key, merror in self._m.merrors.items()
                               if merror.at_lower_limit],
            'at_upper_limit': [key for key, merror in self._m.merrors.items()
                               if merror.at_upper_limit],
            'errors': {key: (merror.lower, merror.upper) for key, merror in
                       self._m.merrors.items()}
            }
        }
        self.append_to_log(log)
        return result

    @property
    def fixed(self) -> dict:
        return [key for key, fixed in self._m.fixed.to_dict().items() if fixed]

    def append_to_log(self, log: dict):
        # To keep the log as valid json, the ending '}' of the file and
        # the beginning '{' of the new json dict must be removed
        string = json.dumps(log, **self.json_settings)
        eof = self._logfile.seek(0, 2)
        self._logfile.seek(eof - 2) # file ends in }\n
        self._logfile.write(f',{string[1:]}')
        self.update_infoline()

    def update_infoline(self):
        """Update the first line so in gives the count for each function.
        This relies on the length of the first line staying constant, so
        using json.dumps is risky.
        """
        if any([c > 99 for c in self._counter.values()]):
            # The digit limit is easy to change and 99 should be plenty.
            raise ValueError("Cannot log more than 99 calls in one file. "
                             f"Counters are currently {self._counter}.")
        infoline = (
            '{ "total_calls": {'
            f'"migrad":{self._counter["migrad"]:3d}, '
            f'"hesse":{self._counter["hesse"]:3d}, '
            f'"minos":{self._counter["minos"]:3d}'
            '}'
            )
        self._logfile.seek(0)
        self._logfile.write(infoline)


@define
class MinuitLog:
    """Read and extract data from the writte log file.
    """
    migrad: list
    hesse: list
    minos: list

    @classmethod
    def from_file(cls, file: TextIO | Path | str):
        if isinstance(file, str | Path):
            with open(file) as infile:
                log = json.load(infile)
        else:
            log = json.load(file)
        return cls.from_log(log)

    @classmethod
    def from_log(cls, log: dict):
        migrad = []
        hesse = []
        minos = []
        for key, value in log.items():
            match key.split('_')[0]:
                case "migrad":
                    migrad.append(value)
                case "hesse":
                    hesse.append(value)
                case "minos":
                    minos.append(value)
        return cls(migrad, hesse, minos)

    def extract_minima(self, call: int, peak: int, spectrum: int) -> dict:
        return {
            key.split('_')[0]: float(value) for key, value
            in self.migrad[call]['minimum'].items()
            if key.split('_')[1] in (str(peak), '*')
                and key.split('_')[2] in (str(spectrum), '*')
            }
