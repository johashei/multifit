#!/usr/bin/python3

"""fit_spectra.

Usage:
    fit_spectra <config> <log> (--new | --overwrite | --append)
                [--tries <int>] [--strategy <int>] [--minos <str>...]
                [--retries <int>] [--printargs]
    fit_spectra (-h | --help)

Options:
    -h --help           Show this help screen and exit.
    --new               Write a new log file. Will raise an error if the
                        file already exists.
    --overwrite         Overwrite previous log file.
    --append            Append to previous log file.
    --tries <int>       Number of times to run the migrad minimiser before
                        giving up. [default: 5]
    --strategy <int>   Strategy to use for the minimisation. Choices are
                        0 (fast), 1,  2 (careful). See iminuit documentation
                        for details. [default: 1]
    --minos <str>...    Calculate minos errors for the given parameters, or
                        use 'all' for all parameters (not usually necessary).
                        This can take several minutes.
    --retries <int>     Rerun migrad this number of times after a minimum
                        has been found. [default: 0]
    --printargs         Print arguments and exit. (For debug purposes.)
"""

import sys

from docopt import docopt
import numpy as np

from .model import Model
from .data import Spectrum
from .fitter import Fitter
from .interface import load_config, fetch_spectra, import_cdf
from ..loggedminuit import LoggedMinuit


def main():
    args = docopt(__doc__)
    if args['--printargs']:
        print(args)
        sys.exit()

    config = load_config(args['<config>'])
    fitter = Fitter.from_config(config)

    if args['--new']:
        openmode = 'x'
    elif args['--overwrite']:
        openmode = 'w'
    elif args['--append']:
        openmode = 'a'

    try:
        mask = config['fit']['mask']
    except KeyError:
        pass
    else:
        fitter.mask = eval(mask)
    with open(args['<log>'], openmode) as logfile:
        run_fit(args, fitter, logfile)

def run_fit(args, fitter, logfile):
        minuit = LoggedMinuit(fitter.minuit, logfile)
        minuit.strategy = int(args['--strategy'])
        maxtries = int(args['--tries'])
        tries = 0
        while not (minuit.valid or tries >= maxtries):
            tries += 1
            print("Running migrad ... ", file=sys.stderr)
            minuit.migrad()
            minuit.hesse()
        retries = int(args['--retries'])
        while retries > 0:
            tries += 1
            retries -= 1
            print("Rerunning migrad ...", file=sys.stderr)
            minuit.migrad()
            minuit.hesse()

        print(f"Fit {('succeeded' if minuit.valid else 'failed')} "
              f"after {tries} tries.\n"
              f"Reduced χ²: {minuit.fmin.reduced_chi2}", file=sys.stderr)

        if minuit.valid and args['--minos']:
            print(f"Calculating minos errors for {args['--minos']}. "
                  "This can take several minutes.", file=sys.stderr)
            if args['--minos'][0] == 'all':
                minuit.minos()
            else:
                minos_parameters = [
                    key for key in minuit.parameters
                    if key.split('_')[0] in args['--minos']
                    ]
                minuit.minos(*minos_parameters)
            failed = [key for key, merror in minuit.merrors.items()
                      if not merror.is_valid]
            if failed:
                print(f"Minos failed for the following parameters:\n{failed}", file=sys.stderr)
            else:
                print("Minos succeeded for all parameters.", file=sys.stderr)


if __name__ == '__main__':
    main()
