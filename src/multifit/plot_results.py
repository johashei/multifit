#!/usr/bin/python3

"""plot_results.

Usage:
    plot_results CONFIG LOG [options]
    plot_results (-h | --help)

Options:
    -h --help               Show this help screen and exit.
    -v                      Print extra info
    -c --colormap <str>     Name of the colormap to use. [default: cmc.lajolla_r]
    -x --xlabel <str>       Label for the x axis. [default: value]
    -y --ylabel <str>       Label for the y axis. [default: counts / $bin^{-1}$]
    --callnumber <int>      Call to migrad whose result should be plotted,
                            numbered from 1. [default: -1]
    --offset <int>          Offset between the baseline of each spectrum.
                            If unspecified it is calculated from the y
                            limits of the spectra. This is usually too much.
    --printargs             Print arguments and exit. (For debug purposes.)
"""

import json
import sys
from typing import Iterable

from docopt import docopt
import cmcrameri as cmc
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
import numpy as np

from .model import Model
from .data import Spectrum
from .input import load_config, fetch_data, import_cdf
from .utils import exponent
from .plot_tools import get_cycler_from_cmap

def main():
    args = docopt(__doc__)
    if args['--printargs']:
        print(args)
        sys.exit()

    config = load_config(args['CONFIG'])
    with open(args['LOG'], 'r') as infile:
        log = json.load(infile)

    # Modulus allows for reverse indexing
    call = int(args['--callnumber']) % (log['total_calls']['migrad'] + 1)
    spectra = fetch_data(config.data, cls=Spectrum)
    bin_width = config.data.bin_width
    pdf = approximate_pdf(import_cdf(config.model.module, config.model.function), dx=1)
    offset, ygridsep = define_grid(args['--offset'], spectra)
    x = np.linspace(
        config.fit.range[0],
        config.fit.range[-1],
        int((config.fit.range[-1] - config.fit.range[0])/0.2)
        )

    fig, ax = plt.subplots(figsize=(5, 8))
    ax.set_prop_cycle(get_cycler_from_cmap(
        plt.get_cmap(args['--colormap']), len(spectra), 0.1, 0.9))

    plot_spectra(ax, spectra, offset)

    component_colors = plt.get_cmap('cmc.devonS') 
    for i in range(len(spectra)):
        baseline = i*offset
        sum_components = 0
        for j in range(config.fit.number_of_peaks):
            parameters = extract_parameters(
                log,
                call=call,
                peak=j,
                spectrum=i)
            components = (
                pdf(x, return_components=True, **parameters)*bin_width
                )
            sum_components += np.sum(components, axis=1)
            if j == 0 or np.sum(components[:, 0]) != 0:
                background = components[:, 0] + baseline
            for component in components[:, 1:].T:
                # TODO: this might be a good use case for colour jitter
                ax.plot(x, component + background, color=component_colors(10*j))
            ax.plot(x, background, color='green', lw=1)
        ax.plot(x, sum_components + baseline, 'k--',)

    set_aesthetics(ax, offset, ygridsep, args)

    if args['-v']:
        try:
            for key, value in log[f'hesse_{call}']['covariance, correlation'].items():
                var1, var2 = key[1:-1].split(', ')
                if 'Q' in key and var1 != var2 and abs(value[1]) > 0.2:  # more than 20% correlation
                    print(f"{key} : {value}")
        except KeyError as e:
            print(e)
            print("No verbosity implemented for this log. Sorry.")

    plt.show()


def set_aesthetics(ax, offset: int, ygridsep: int | None, args: dict):
    ax.set_yticks(np.arange(*ax.get_ylim(), offset), labels=[])
    if ygridsep:
        ax.set_yticks(np.arange(*ax.get_ylim(), ygridsep), minor=True, labels=[])
        text = ax.annotate(f"Gridlines every {ygridsep}",
                           xy=(1, 1), xycoords='axes fraction',
                           ha='right', va='bottom')
    else:
        ax.yaxis.set_minor_locator(MaxNLocator(
            len(ax.yaxis.get_major_ticks())*5))
        ax.yaxis.set_minor_formatter(FuncFormatter(
            lambda x, pos: f'${x}$' if x < offset else None))
        text = None
    ax.tick_params(which='both', left=False)
    ax.grid(which='both', axis='y', linestyle='-', linewidth=0.2, color='k')
    ax.spines[['left', 'right', 'top']].set_visible(False)
    ax.set_xlabel(args['--xlabel'])
    ax.set_ylabel(f"{args['--ylabel']}",
                  rotation=0, ha='left', va='bottom')
    ax.yaxis.set_label_coords(0, 1)
    return text

def plot_spectra(ax: plt.Axes, spectra: Iterable[Spectrum], offset: int):
    fills = [0]*len(spectra)
    lines = [0]*len(spectra)
    for i, spectrum in enumerate(spectra):
        baseline = i*offset
        fills[i] = ax.stairs(spectrum.counts + baseline, spectrum.bin_edges,
                             baseline=baseline, fill=True, alpha=0.5)
        lines[i] = ax.stairs(spectrum.counts + baseline, spectrum.bin_edges,
                             baseline=baseline, fill=False, color=None,
                             linestyle='-', linewidth=0.5, edgecolor='k',
                             zorder=2)
    return fills, lines

def define_grid(
        offset: str | None,
        spectra: Iterable[Spectrum],
        max_gridlines: int = 5):
    if offset is None:
        offset = get_offset_from_spectra(spectra)
    else:
        offset = int(offset)
    div = offset/(max_gridlines - 1)/10**exponent(offset)
    if div < 1.5:
        gridsep = 1
    elif div < 3:
        gridsep = 2
    elif div < 7:
        gridsep = 5
    else:
        gridsep = 10
    gridsep *= 10**exponent(offset)
    offset = round(offset/gridsep)*gridsep
    return offset, gridsep

def get_offset_from_spectra(spectra: Iterable[Spectrum]):
    lower = spectra[0].counts.min()
    upper = spectra[0].counts.max()
    for spectrum in spectra[1:]:
        if (new := spectrum.counts.min()) < lower:
            lower = new
        if (new := spectrum.counts.max()) > upper:
            upper = new
    yrange = upper - lower
    return int(yrange)

def approximate_pdf(cdf, dx) -> callable:
    def pdf(x, *args, **kwargs):
        return (cdf(x + dx/2, *args, **kwargs)
                - cdf(x - dx/2, *args, **kwargs)
                )/dx
    return pdf

def extract_parameters(log: dict, call: int, peak: int, spectrum: int) -> dict:
    try:
        return {
            key.split('_')[0]: float(value) for key, value # njit requires float
            in log[f'migrad_{call}']['minimum'].items()
            if key.split('_')[1] in (str(peak), '*')
                and key.split('_')[2] in (str(spectrum), '*')
            }
    except IndexError:
        # unique parameters formatted as x, not as x_*_*
        parameters = {}
        for key, value in log[f'migrad_{call}']['minimum'].items():
            splitkey = key.split('_')
            if len(splitkey) == 1:
                parameters[splitkey[0]] = float(value)
            elif (splitkey[1] in (str(peak), '*')
                  and splitkey[2] in (str(spectrum), '*')):
                parameters[splitkey[0]] = float(value)
        return parameters

if __name__ == '__main__':
    main()
