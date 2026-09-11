#!/usr/bin/python3
"""multifit command line interface

Usage: multifit [--version] [--copying] [--help] COMMAND [ARGS...]

Options:
    -h --help       Print the help screen for the given command and exit.
    --version       Print version number and exit.
    --copying       Print copyright notice and exit.

List of commands:
    config          Generate a new config file.
    fit             Fit a set of spectra.
    gate            Run a GUI for gating on coincidence spectra.
    plot            Plot a set of spectra, optionally including a fit result.

See multifit help COMMAND for more information on a specific command.

Copyright (C) 2026 Johannes Sørby Heines
"""

from docopt import docopt

from .__about__ import __version__, __copying__

def main():
    args = docopt(__doc__, version=__version__, options_first=True)

    if args['--copying']:
        print(__copying__)
        return

    command = args['COMMAND']
    command_args = args['ARGS']

    match command:
        case 'config':
            from .config import main
            main()

        case 'fit':
            from .fit import main
            main()

        case 'gate':
            from .gate import main
            main()

        case 'plot':
            from .plot import main
            main()


if __name__ == '__main__':
    main()
