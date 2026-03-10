#!/usr/bin/python3
"""
Usage: multifit plot CONFIG [LOG] [--color MAP] [--xlabel LABEL]
                     [--ylabel LABEL] [--callnumber N] [--background INDEX]

    -h --help           Print this help screen and exit.

Plotting options:
    -c --color MAP      Name of the colormap to use. [default: viridis]
    -x --xlabel LABEL   Label on the x axis. [default: value]
    -y --ylabel LABEL   Label on the y axis. [default: counts per bin]

Fit selection options: (only relevant if LOG is provided)
    --callnumber N      Number of the migrad iteration to plot. Starts
                        at 1, supports reverse indexing. [default: -1]
    -b --background INDEX
                        Use this component of the model cdf as the
                        background when plotting.
"""
from functools import partial

from docopt import docopt
import matplotlib.pyplot as plt
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.widgets import Slider, Cursor
import numpy as np

from .data import Spectrum
from .input import Config, fetch_data, import_cdf
from .loggedminuit import MinuitLog
from .plot_tools import (
        FigureWithWidgets, Histogram, get_cycler_from_cmap, Density
        )

def main():
    args = docopt(__doc__)

    # the plot functionality should work even with an incomplete config
    config = Config.from_yaml(args['CONFIG'], error_if_incomplete=False)
    spectra = fetch_data(config.data, cls=Spectrum)

    # make figure
    max_spectrum_height = max([np.nanmax(spc.counts) for spc in spectra])
    fig, [ax, _] = make_interactive_figure(max_offset=max_spectrum_height)

    # set color cycle
#    ax.set_prop_cycle(get_cycler_from_cmap(
#        plt.get_cmap(args['--color']), len(spectra), 0.1, 0.9))

    # draw the data
    histograms = [Histogram.from_spectrum(spc, ax) for spc in spectra]

    # read and draw the fit result
    if (logfile := args['LOG']):
        with open(logfile, 'r') as infile:
            log = MinuitLog.from_file(infile)

        pdf = partial(
            approximate_pdf(import_cdf(
                    config.model.module,
                    config.model.function
                    ),
                1e-3),
            )

        if args['--background']:
            background_index = int(args['--background'])
        else:
            background_index = None
        x = np.arange(*config.fit.range, config.data.bin_width/5)
        densities = []
        for peak_number in range(config.model.number_of_peaks):
            for spect_number in range(len(spectra)):
                parameters = log.extract_minima(
                    int(args['--callnumber']),
                    peak_number,
                    spect_number
                    )
                densities.append(Density.from_data(
                    x,
                    pdf(x, **parameters, **config.model.kwargs),
                    ax,
                    background_index
                    ))
                densities[-1].background.set_color('k')
    else:
        densities = None

    # initialize the update function
    update_offset_ax = partial(
        update_offset,
        ax=ax,
        histograms=histograms,
        densities=densities
        )
    update_offset_ax(max_spectrum_height/2)
    fig.widgets['slider'].on_changed(update_offset_ax)

    # set initial ylim
    ax.set_ylim([0, max_spectrum_height/2*(len(spectra)+1)])


    plt.show()


def make_interactive_figure(max_offset):
    fig, [ax_plot, ax_slider] = plt.subplots(
        ncols=2,
        figsize=(9, 12),
        layout='constrained',
        width_ratios=[0.95, 0.05]
        )
    slider = Slider(
        ax=ax_slider,
        label='spectrum\nseparation',
        valmin=0,
        valmax=max_offset,
        valinit=max_offset/2,
        orientation="vertical"
        )
    cursor = Cursor(
        ax_plot,
        horizOn=False,
        vertOn=True,
        useblit=True,
        color='k',
        linestyle=':',
        linewidth=0.8
        )
    # Monkeypatch the widgets onto the figure so they stay in scope
    fig.widgets = {'slider': slider, 'cursor': cursor}
    return fig, [ax_plot, ax_slider]

# previous_val is a list because it needs to persist between
# functions calls but I cannot catch it as a return value.
# It is 0 because the histograms are initialized with no baseline offset.
def update_offset(val, ax, histograms, densities, previous_val=[0]):
    for i, histogram in enumerate(histograms):
        histogram.set_baseline(i*val)
    if densities:
        for i, density in enumerate(densities):
            density.set_baseline(i*val)
    # setting the yticks also sets ylim to include all ticks. This
    # means calling this function automatically ensures all spectra
    # are visible.
    try:
        ax.set_yticks(np.arange(0, (i+1)*val, val)) #, labels=[])
    except ZeroDivisionError:
        ax.set_yticks([0], labels=[])
    # update ylim so the top and bottom points stay the same
    # previous_val is a list so it can be updated by the function, since
    # I cannot catch it's return value
    ylim = ax.get_ylim()
    ax.set_ylim((ylim[0], ylim[1] + (val - previous_val[0])*i))
    previous_val[0] = val
#    ygridsep = gridsep_from_offset(val)
#    major_ticks, minor_ticks = sliding_grid(
#        major_sep=val,
#        minor_sep=ygridsep,
#        major_start=0,
#        major_stop=(i + 1)*val)  # using the last, thus highest, value of i
#    ax.set_yticks(major_ticks[:-1], labels=[])
#    ax.set_yticks(minor_ticks, minor=True, labels=[])
#    grid_info.set_text(f"Gridelines every {ygridsep}")

def approximate_pdf(cdf: callable, h: float) -> callable:
    # simple numerical differentiation
    def pdf(x, *args, **kwargs):
        return (cdf(x + h, *args, **kwargs) - cdf(x - h, *args, **kwargs))/2/h
    return pdf

if __name__ == '__main__':
    main()
