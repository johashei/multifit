#!/usr/bin/python3
"""
Usage: multifit plot CONFIG [LOG] [--color MAP] [--xlabel LABEL]
                     [--ylabel LABEL] [--callnumber N]

    -h --help           Print this help screen and exit.

Plotting options:
    -c --color MAP      Name of the colormap to use. [default: viridis]
    -x --xlabel LABEL   Label on the x axis. [default: value]
    -y --ylabel LABEL   Label on the y axis. [default: counts per bin]

Fit selection options: (only relevant if LOG is provided)
    --callnumber N      Number of the migrad iteration to plot. Starts
                        at 1, supports reverse indexing. [default: -1]
"""
from docopt import docopt

def main():
    args = docopt(__doc__)

    if args['LOG']:
        from .plot_results import main
        main()
    else:
        from .plot_spectra import main
        main()

if __name__ == '__main__':
    main()
