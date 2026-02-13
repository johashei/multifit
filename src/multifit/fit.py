#!/usr/bin/python3

"""
Usage: multifit fit CONFIG LOG (--new | --overwrite | --append)
                    [-v] [--minos PARAM...] [--strategy N] [--tries N]
                    [--retries N] [--printargs]

    -h --help           Show this help screen and exit.
    -v --verbose        Print runtime information.
    --new               Write a new log file. Will raise an error if the
                        file already exists.
    --overwrite         Replace an existing log file .
    --append            Append to an existing log file.
    --tries N           Number of times to run the migrad minimiser
                        before giving up. [default: 5]
    --strategy N        Strategy to use for the minimisation. Choices are
                        0 (fast), 1,  2 (careful). See the iminuit
                        documentation for details. [default: 1]
    --minos PARAM...    Calculate minos errors for the given parameters,
                        or use 'all' for all parameters (not usually
                        necessary). This can take several minutes.
    --retries N         Rerun migrad this number of times after a minimum
                        has been found. [default: 0]
"""

from functools import partial
import sys

from docopt import docopt
import numpy as np

from .fitter import Fitter
from .model import Model
from .data import Spectrum
from .input import load_config, fetch_data
from .loggedminuit import LoggedMinuit


def main():
    args = docopt(__doc__)

    config = load_config(args['CONFIG'])
    spectra = fetch_data(config.data, cls=Spectrum)
    model = Model.from_config(config.model)
    fitter = Fitter.from_config(spectra, model, config.fit)

    if args['--new']:
        openmode = 'x'
    elif args['--overwrite']:
        openmode = 'w'
    elif args['--append']:
        openmode = 'a'

    try:
        mask = config.fit.mask
    except KeyError:
        pass  # mask key is optional in the config file.
    else:
        fitter.mask = eval(mask)  # I trust you know what you're doing
    with open(args['LOG'], openmode) as logfile:
        minuit = run_fit(
            fitter,
            logfile,
            maxtries=int(args['--tries']),
            minos=args['--minos'],
            retries=int(args['--retries']),
            strategy=int(args['--strategy']),
            verbose=args['--verbose']
            )
    print(minuit)

# Separated from main so fits can be run from another program
def run_fit(
        fitter,
        logfile,
        maxtries=5,
        minos=None,
        retries=0,
        strategy=1,
        verbose=False,
        ):
    if verbose:
        vprint = partial(print, file=sys.stderr)
    else:
        vprint = lambda _: None  # silent
    minuit = LoggedMinuit(fitter.minuit, logfile)
    minuit.strategy = strategy
    tries = 0
    while not (minuit.valid or tries >= maxtries):
        tries += 1
        vprint("Running migrad ... ")
        minuit.migrad()
        minuit.hesse()
    while retries > 0:
        tries += 1
        retries -= 1
        vprint("Rerunning migrad ...")
        minuit.migrad()
        minuit.hesse()

    vprint(f"Fit {('succeeded' if minuit.valid else 'failed')} "
          f"after {tries} tries.\n"
          f"Reduced χ²: {minuit.fmin.reduced_chi2}")

    if minuit.valid and minos:
        vprint(f"Calculating minos errors for {minos}. "
              "This can take several minutes.")
        if minos[0] == 'all':
            minuit.minos()
        else:
            minos_parameters = [
                key for key in minuit.parameters
                if key.split('_')[0] in minos
                ]
            minuit.minos(*minos_parameters)
        failed = [key for key, merror in minuit.merrors.items()
                  if not merror.is_valid]
        if failed:
            vprint(f"Minos failed for the following parameters:\n{failed}")
        else:
            vprint("Minos succeeded for all parameters.")
        # Print full report from iminuit
        return minuit


if __name__ == '__main__':
    main()
