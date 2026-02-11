#!/usr/bin/python3

"""plot_spectra.

Usage:
    plot_spectra <config> [options]
    plot_spectra (-h | --help)

Options:
    -h --help             Show this help screen and exit
    -c --colormap <str>   Name of the colormap to use. [default: cmc.lajolla_r]
    -x --xlabel <str>     Label for the x axis. [default: value]
    -y --ylabel <str>     Label for the y axis. [default: counts per bin]
    -g --gridsep <int>    Fixed separation of the gridlines on the y axis.
    --printargs           Print arguments and exit. (For debug purposes.)
"""

import sys

import cmcrameri as cmc
from docopt import docopt
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Cursor
import numpy as np

from .data import Spectrum
from .interface import load_config, fetch_spectra
from .utils import exponent
from .plot_tools import (
    get_cycler_from_cmap,
    get_offset_from_spectra,
    plot_spectra,
    set_aesthetics,
    InteractivePlot,
    gridsep_from_offset,
    sliding_grid
    )

def main():
    args = docopt(__doc__)
    if args['--printargs']:
        print(args)
        sys.exit()
    plot = make_interactive_plot(args)
    plt.show()

def make_interactive_plot(args):
    config = load_config(args['<config>'], check_completeness=False)

    spectra = fetch_spectra(config, 0)
    bin_width = config['data']['bin_width']

    max_offset = get_offset_from_spectra(spectra)
    offset = max_offset/2
    if args['--gridsep']:
        ygridsep = int(args['--gridsep'])
    else:
        ygridsep = gridsep_from_offset(offset)

    fig, ax = plt.subplots(figsize=(6, 8))
    ax.set_prop_cycle(get_cycler_from_cmap(
        plt.get_cmap(args['--colormap']), len(spectra), 0.1, 0.9))

    fills, lines = plot_spectra(ax, spectra, offset)

    grid_info = set_aesthetics(ax, offset, ygridsep, args)

    # Add slider to control offset
    fig.subplots_adjust(left=0.1, bottom=0.1, top=0.9, right=0.75)  # make room for slider
    slider_ax = fig.add_axes([0.85, 0.12, 0.02, 0.75])
    slider = Slider(
        ax=slider_ax,
        label='spectrum\nseparation',
        valmin=1,
        valmax=max_offset,
        valinit=offset,
        orientation="vertical")

    previous_val = [offset]  # so I can change it from within a function
    def update_offset(val):
        for i, (line, fill, spectrum) in enumerate(zip(lines, fills, spectra)):
            line.set_data(values=spectrum.counts + i*val, baseline=i*val)
            fill.set_data(values=spectrum.counts + i*val, baseline=i*val)
        ygridsep = gridsep_from_offset(val)
        major_ticks, minor_ticks = sliding_grid(
            major_sep=val,
            minor_sep=ygridsep,
            major_start=0,
            major_stop=(i + 1)*val)  # using the last, thus highest, value of i
        ax.set_yticks(major_ticks[:-1], labels=[])
        ax.set_yticks(minor_ticks, minor=True, labels=[])
        grid_info.set_text(f"Gridelines every {ygridsep}")
        # Changing the ylim here isn’t a good idea. Or is it?
        ylim = ax.get_ylim()
        ax.set_ylim((ylim[0], ylim[1] + (val - previous_val[0])*i))
        previous_val[0] = val

    slider.on_changed(update_offset)

    cursor = Cursor(ax, horizOn=False, vertOn=True, useblit=True,
                    color='k', linestyle=':', linewidth=0.5)

    return InteractivePlot(fig, {'slider': slider, 'cursor': cursor})

if __name__ == '__main__':
    main()
