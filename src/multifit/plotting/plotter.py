# Should this be its own module?
from itertools import cycle
from typing import Iterable

import cmcrameri as cmc
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
import numpy as np

from ..data import Spectrum
from ..utils import bin_edges_iff_equal
from .utils import get_cycler_from_cmap


class IntervalSelectorGUI:
    def __init__(self, spectra: Iterable[Spectrum]):
        """"""
        self.spectra = spectra
        # If the spectra have different bin edges, raise ValueError:
        self.bin_edges = bin_edges_iff_equal(spectra)

    def run_widget(self):
        """"""
        fig, axes = plot_spectra(self.spectra)
        fig.subplots_adjust(top=0.9)
        span = SpanSelector(
            axes[0], self.onselect, 'horizontal',
            useblit=True,
            interactive=True,
            snap_values=self.bin_edges)

def plot_spectra(
        spectra: Iterable[Spectrum], *,
        xlabel: str = 'Value',
        ylabel: str = 'Counts',
        subplots_kwargs: dict | None = None,
        plot_kwargs: dict | None = None):
    """Make staked plots of spectra"""
    default_subplots_kwargs = {
        'figsize': (7,8.5),
        'sharex': True,
        'sharey': True,
        'layout': None,
        'gridspec_kw': {
            'hspace': -0.4,
            'top': 0.99,
            'bottom': 0.1
            },
        'subplot_kw': {
            'facecolor': 'none',
            'yticks': [1e3],
            },
        }
    default_plot_kwargs = {
        }
    if subplots_kwargs is None:
        subplots_kwargs = default_subplots_kwargs
    else:
        subplots_kwargs = default_subplots_kwargs | subplots_kwargs
    if plot_kwargs is None:
        plot_kwargs = default_plot_kwargs
    else:
        plot_kwargs = default_plot_kwargs | plot_kwargs
    colors = cycle(get_cycler_from_cmap(
            plt.get_cmap('cmc.lajolla_r'), len(spectra), 0.1, 0.9)
        .by_key()['color'])

    fig, axes = plt.subplots(len(spectra), 1, **subplots_kwargs)
    for ax, spectrum in zip(axes, spectra):
        ax.grid(which='major', axis='y')
        ax.get_xaxis().set_visible(False)
        ax.tick_params(axis='y', left=False, labelleft=False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.stairs(spectrum.counts, spectrum.bin_edges,
                  color = next(colors),
                  **plot_kwargs)

    axes[-1].spines['bottom'].set_visible(True)
    axes[-1].get_xaxis().set_visible(True)
    axes[-1].set_xlabel(xlabel)
    axes[0].set_ylabel(ylabel)

    return fig, axes
