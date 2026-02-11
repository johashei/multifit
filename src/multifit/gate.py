#!/usr/bin/python3
"""
Usage: multifit gate CONFIG [options]

    -h --help           Print this help screen and exit.
    -e --export PATH    Default export location for gated spectra.

Plotting options:
    -c --color MAP      Name of the colormap to use. [default: cmc.lajolla_r]
    -x --xlabel LABEL   Label for the x axis. [default: value]
    -y --ylabel LABEL   Label for the y axis. [default: counts per bin]
    -g --gridsep VALUE  Fixed separation of the gridlines on the y axis.

Debugging options:
    --printargs         Print arguments and exit.
"""

from functools import partial
import math
from pathlib import Path
import sys

import cmcrameri as cmc
from docopt import docopt
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Cursor, RangeSlider, Button, TextBox
import numpy as np

from .data import CoincidenceMatrix
from .interface import load_config, fetch_data
from .plot_tools import plot_spectra, get_cycler_from_cmap, InteractivePlot
from .plot_tools import get_offset_from_spectra, RangeMarker, eventsoff

def main():
    args = docopt(__doc__)
    if args['--printargs']:
        print(args)
        sys.exit()
    plot = make_interactive_plot(args)
    plt.show()

def make_interactive_plot(args):
    config = load_config(args['CONFIG'], check_completeness=False)

    if not (default_export_path := args['--export']):
        default_export_path = config['data']['directory']

    matrices = fetch_data(
        config,
        key=lambda file: file.rsplit('.', 1)[0],
        cls=CoincidenceMatrix,
        npy=True
        )
    bin_width = config['data']['bin_width']
    min_bin_edge = matrices[0].bin_edges[0]
    max_bin_edge = matrices[0].bin_edges[-1]

    spectra = []
    for matrix in matrices:
        spectra.append(matrix.gate(min_bin_edge, max_bin_edge))

    max_offset = get_offset_from_spectra(spectra)
    offset = max_offset/2

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.subplots_adjust(left=0.1, right=0.8, bottom=0.2, top=0.9)
    ax.set_prop_cycle(get_cycler_from_cmap(
        plt.get_cmap(args['--color']), len(spectra), 0.1, 0.9
        ))
    ax.set_yticks([])
    ax.spines[['left', 'right', 'top']].set_visible(False)
    ax.set_xlabel(args['--xlabel'])
    ax.set_ylabel(f"{args['--ylabel']}", rotation=0, ha='left', va='bottom')
    ax.yaxis.set_label_coords(0, 1)

    gate_slider_ax = fig.add_axes([0.2, 0.1, 0.6, 0.02], sharex=ax)
    gate_slider_ax.set_title("Slide to define a gate")
    gate_textbox_ax1 = fig.add_axes([0.81, 0.135, 0.09, 0.025])
    gate_textbox_ax2 = fig.add_axes([0.81, 0.1, 0.09, 0.025])
    gater_ax = fig.add_axes([0.1, 0.1, 0.09, 0.07])
    offsetter_ax = fig.add_axes([0.84, 0.2, 0.02, 0.7])
    export_button_ax = fig.add_axes([0.1, 0.93, 0.2, 0.03])
    export_location_ax = fig.add_axes([0.35, 0.93, 0.45, 0.03])
    notification = fig.text(0.35, 0.905, '')

    fills, lines = plot_spectra(ax, spectra, offset)
    gate_selection_marker = RangeMarker(
        [min_bin_edge, max_bin_edge], ax=ax, axis='x', ls='--', c='k'
        )
    gate_applied_marker = RangeMarker(
        [min_bin_edge, max_bin_edge], ax=ax, axis='x', ls='--', c='r'
        )

    gate_selector = RangeSlider(
        ax=gate_slider_ax,
        label="",
        valmin=min_bin_edge,
        valmax=max_bin_edge,
        valstep=bin_width,
        closedmin=False,
        closedmax=False,
        orientation='horizontal',
        valfmt='',
        )
    gate_textbox_min = TextBox(
        ax=gate_textbox_ax1,
        label='',
        initial=f"{gate_selector.val[0]}"
        )
    gate_textbox_max = TextBox(
        ax=gate_textbox_ax2,
        label='',
        initial=f"{gate_selector.val[1]}",
        )
    gater = Button(
        ax=gater_ax,
        label="Click to\napply\ngate",
        useblit=True
        )
    offsetter = Slider(
        ax=offsetter_ax,
        label="Spectrum\nseparation\n(logarithmic)",
        valmin=1,
        valmax=math.log(max_offset),
        valinit=math.log(offset),
        orientation='vertical',
        )
    export_location = TextBox(
        ax=export_location_ax,
        label='',
        initial=default_export_path
        )
    export_button = Button(
        ax=export_button_ax,
        label="export spectra"
        )
    cursor = Cursor(ax, horizOn=False, vertOn=True, useblit=True,
                    color='k', linestyle=':', linewidth=0.5)

    @eventsoff(gate_textbox_min, gate_textbox_max)
    def update_gate_textbox(gate: tuple[float, float]):
        gate_textbox_min.set_val(f"{gate[0]}")
        gate_textbox_max.set_val(f"{gate[1]}")
        gate_selection_marker.range = gate

    @eventsoff(gate_selector)
    def update_gate_selector(expression: str, which: int):
        gate = list(gate_selection_marker.range)
        gate[which] = float(expression)
        gate_selector.set_val(gate)
        gate_selection_marker.range = gate

    def update_spectra(_):
        for i, matrix in enumerate(matrices):
            spectra[i] = matrix.gate(*gate_selector.val)
        offset = get_offset_from_spectra(spectra)
        offsetter.set_val(math.log(offset))
        for i, (line, fill, spectrum) in enumerate(zip(lines, fills, spectra)):
            line.set_data(values=spectrum.counts + offset*i, baseline=offset*i)
            fill.set_data(values=spectrum.counts + offset*i, baseline=offset*i)
        ax.set_ylim([0, offset*(i + 1)])
        gate_applied_marker.range = gate_selector.val

    previous_offset = [offset]  # so I can change it from within a function
    def update_offset(val):
        offset = math.exp(val)
        for i, (line, fill, spectrum) in enumerate(zip(lines, fills, spectra)):
            line.set_data(values=spectrum.counts + i*offset, baseline=i*offset)
            fill.set_data(values=spectrum.counts + i*offset, baseline=i*offset)
        ylim = ax.get_ylim()
        ax.set_ylim((ylim[0], ylim[1] + (offset - previous_offset[0])*i))
        previous_offset[0] = offset

    def export_spectra(_):
        try:
            location = export_location.text
            gate = gate_selection_marker.range
            path = f"{location.rstrip('/')}/gate_{gate[0]}-{gate[1]}"
            Path(path).mkdir(parents=True, exist_ok=False)
            for spectrum in spectra:
                npfile = f"{path}/{spectrum.key}.npy"
                np.save(npfile, spectrum.counts, allow_pickle=False)
        except BaseException as e:
            notification.set(text=str(e), color='r')
            raise e
        else:
            msg = f"Saved spectra to {path}"
            notification.set(text=msg, color='g')
            print(msg)
        plt.draw()


    gate_selector.on_changed(update_gate_textbox)
    gate_textbox_min.on_submit(partial(update_gate_selector, which=0))
    gate_textbox_max.on_submit(partial(update_gate_selector, which=1))
    gater.on_clicked(update_spectra)
    offsetter.on_changed(update_offset)
    export_button.on_clicked(export_spectra)

    return InteractivePlot(
        fig, {
            'gate_slider': gate_selector,
            'gate_textbox_min': gate_textbox_min,
            'gate_textbox_max': gate_textbox_max,
            'gate_button': gater,
            'offset_slider': offsetter,
            'export_button': export_button,
            'export_textbox': export_location,
            'cursor': cursor
        })

if __name__ == '__main__':
    main()
