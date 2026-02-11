from typing import Iterable

from attrs import define, field
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
from matplotlib.widgets import Slider, Cursor
import numpy as np

from ..data import Spectrum
from ..utils import exponent

@define
class InteractivePlot:
    """A dataclass to contain a Figure with widgets."""
    fig: plt.Figure
    widgets: dict[str, plt.Widget]

class RangeMarker:
    __slots__ = ('_range', '_ax', '_axis', 'min_marker', 'max_marker')
    def __init__(
            self,
            range: tuple[float, float],
            ax: plt.Axes, axis: str,
            **Line2D_kwargs
        ):
        self._range = tuple(range)
        self._ax = ax
        self._axis = axis
        self.mark(Line2D_kwargs)

    @property
    def range(self) -> tuple[float, float]:
#        print('->', self._range)
        return self._range

    @range.setter
    def range(self, value: Iterable[float]):
        self._range = tuple(value)
#        print('<-', self._range)
        if self.axis == 'x':
            self.min_marker.set_xdata([value[0]])
            self.max_marker.set_xdata([value[1]])
        elif self.axis == 'y':
            self.min_marker.set_ydata([value[0]])
            self.min_marker.set_ydata([value[1]])
        else:
            raise ValueError(f"axis must be either x or y, but is {self.axis}."
                             " This message should never display.")

    @property
    def ax(self) -> plt.Axes:
        return self._ax

    @property
    def axis(self) -> str:
        return self._axis

    def mark(self, Line2D_kwargs):
        if self.axis == 'x':
            linefunc = self.ax.axvline
        elif self.axis == 'y':
            linefunc = self.ax.axhline
        else:
            raise ValueError("axis must be either x or y")
        self.min_marker = linefunc(self.range[0], **Line2D_kwargs)
        self.max_marker = linefunc(self.range[1], **Line2D_kwargs)

def eventsoff(*widgets: plt.Widget):
    """Switch off event triggering for the given Widgets."""
    def decorator(func):
        def inner(*args, **kwargs):
            for widget in widgets:
                widget.eventson = False
            return_value = func(*args, **kwargs)
            for widget in widgets:
                widget.eventson = True
            return return_value
        return inner
    return decorator

def get_cycler_from_cmap(cmap, number_of_colors=None, low=0, high=1):
    if not number_of_colors:
        number_of_colors = cmap.N
    points = np.linspace(low, high, int(number_of_colors))
    return plt.cycler('color', cmap(points))
    # TODO: possible improvement: add option for categorical data.

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
    ax.set_ylabel(f"{args['--ylabel']}", rotation=0, ha='left', va='bottom')
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

def sliding_grid(  # TODO: put in its own file
        *,
        major_sep,
        minor_sep,
        major_start,
        major_stop):
    major_ticks = np.arange(major_start, major_stop, major_sep)
    minor_element = np.arange(0, major_sep, minor_sep)
    minor_ticks = (np.broadcast_to(
            minor_element,
            (len(major_ticks), len(minor_element))
        ).T
        + major_ticks).flatten('F')
    return major_ticks, minor_ticks

def gridsep_from_offset(offset):
    size = offset/10**(exponent(offset))
    small_sep = 10**(exponent(offset) - 1)
    if size < 2:
        return 2*small_sep
    elif size < 4:
        return 5*small_sep
    elif size < 7:
        return 10*small_sep
    else:
        return 20*small_sep
