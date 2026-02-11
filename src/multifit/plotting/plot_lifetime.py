"""plot_lifetime.py

Plot the decay curve fit of the lifetime.

Usage:
    plot_lifetime.py <lifetime log file> [-v] [-s <file>] [-w <width] [-p [-o]]

Options:
    -h --help                   Show this help screen and exit.
    -v --verbose                Print lifetime value and uncertainty.
    -p --publication            Generate a plot suited for publication.
    -s <file> --save=<file>     Save the plot to a file. Supported
                                file extensions are:
                                    .pdf
                                    .eps
                                    .pdf_tex (requires matplatex)
    -w <width> --width=<width>  Width of the figure, possible values are:
                                    'half' (half page figure)
                                    'full' (full page figure)
                                    width in mm
                                [default: full]
    -o --output                 Write the figure data to stdout as json,
                                for replotting in a separate program.
"""

import json
from pathlib import Path
import sys

from docopt import docopt
import matplotlib.pyplot as plt
import numpy as np
from uncertainties import ufloat

from ..dcm2 import bsplines

INCHES_PER_MM = 0.03937
HALF_PAGE_WIDTH_MM = 120
FULL_PAGE_WIDTH_MM = 140

def main():
    args = docopt(__doc__)

    # Uso old script until new is done
    if not args['--publication']:
        from .plot_lifetime_old import main as old_main
        with open(args['<lifetime log file>'], 'r') as sys.stdin:
            old_main()
        sys.exit()


    with open (args['<lifetime log file>']) as infile:
        data = json.load(infile)

    match args['--width']:
        case 'full':
            figwidth_inches = FULL_PAGE_WIDTH_MM*INCHES_PER_MM
        case 'half':
            figwidth_inches = HALF_PAGE_WIDTH_MM*INCHES_PER_MM
        case value:
            try:
                figwidth_inches = float(value)*INCHES_PER_MM
            except ValueError:
                print(
                    f"couldn't understand width {value}, using full "
                    f"({FULL_PAGE_WIDTH_MM} mm)",
                    end='\n',
                    file=sys.stderr
                    )
                figwidth_inches = FULL_PAGE_WIDTH_MM*INCHES_PER_MM

    if args['--publication']:
        plt.rc('lines', lw=1)
        if 'feeder' in data['argv']:
            fig = make_publication_singles_plot(data, figwidth_inches)
        else:
            fig = make_publication_coinc_plot(data, figwidth_inches)

    if args['--verbose']:
        lifetime = ufloat(*data['result']['lifetime'])
        half_life = lifetime*np.log(2)
        print(f"τ = {lifetime:P}")
        print(f"t½ = {half_life:P}")

    if args['--save']:
        outfile = Path(args['--save'])
        if outfile.suffix == '.pdf_tex':
            import matplatex
            matplatex.save(fig, str(outfile.parent/outfile.stem))
        else:
            fig.savefig(outfile)

    if args['--output']:
        figure_content = serialize_figure_content(fig)
        json.dump(figure_content, sys.stdout, indent=2)

    plt.show()


# These two functions are quite similar, but last time I tried to refactor
# this it ended up being unreadable and unflexible, so better keep them as is

def make_publication_singles_plot(data, figwidth_inches):
    try:
        time_nodes = np.array(data['time_nodes'])
        time_points = np.array(data['times'])
        time_point_errs = np.array(data['time_errs'])
    except KeyError:
        time_nodes = np.array(data['NODES'])/data['speed']
        time_points = np.array(data['DISTANCES'])/data['speed']
        time_point_errs = np.array(data['DISTANCE_ERRS'])/data['speed']

    figsize = (figwidth_inches, figwidth_inches)

    fig, [feeder_ax, decay_ax, fit_ax] = plt.subplots(
        3, 1, figsize=figsize, sharex=True, layout='tight'
        )
    # IMPORTANT: loop order must be 'feeder' -> 'decay' for logic to work
    for ax, curve_name in zip([feeder_ax, decay_ax], ['feeder', 'decay']):
        # Plot the fitted curves
        x = np.linspace(time_nodes[0], time_nodes[-1], 600)
        spline_weights = np.array([
            # sorted by key to make sure weight order is correct
            val[0] for key, val in sorted(data['result'].items())
            if key.startswith(f'{curve_name}_weight')
            ])
        fit = spline_weights@bsplines.basis(
            data[f'{curve_name}_order'], time_nodes, x, 0
            ).T
        ax.plot(x, fit, '-k')

        # Plot the data points
        ax.errorbar(
            time_points,
            data[f'{curve_name}_data'][0],
            xerr=time_point_errs,
            yerr=data[f'{curve_name}_data'][1],
            linestyle='',
            marker='',
            capsize=3,
            color='k'
            )

        # calculate the difference and derivative in the loop
        if curve_name == 'feeder':
            difference = data['feeding_coeff'][0]*fit
        elif curve_name == 'decay':
            difference -= fit
            derivative = spline_weights@bsplines.basis(
                data[f'{curve_name}_order'], time_nodes, x, 1
                ).T

        # Make good looking axes
        ax.set_ylabel(rf"$R_\mathrm{{{curve_name}}}$",
                      rotation=0, ha='center', va='bottom')
        ax.get_yaxis().set_label_coords(0, 1)
        ax.spines.left.set_bounds(0, 1)
        ax.set_ylim([None, 1])
        adjust_spines(ax, ['left'])

    # Plot the derivative constraint
    lifetime = ufloat(*data['result']['lifetime'])
    fit_ax.plot(x, difference, '-k',
                label=r"$R_\mathrm{feeding} - R_\mathrm{decay}$")
    fit_ax.plot(x, lifetime.nominal_value*derivative, '--k',
                label=r"$\tau\frac{\mathrm{d}}{\mathrm{d}t}R_\mathrm{decay}$")
    fit_ax.legend()

    fit_ax.set_xlabel(f"{data['x_quantity']} / {data['x_unit']}")
    fit_ax.spines.bottom.set_bounds(time_nodes[0], time_nodes[-1])
    adjust_spines(fit_ax, ['left', 'bottom'])

    return fig

def make_publication_coinc_plot(data, figwidth_inches):
    time_nodes = np.array(data['NODES'])/data['speed']
    time_points = np.array(data['DISTANCES'])/data['speed']
    time_point_errs = np.array(data['DISTANCE_ERRS'])/data['speed']

    figsize = (figwidth_inches, 2/3*figwidth_inches)

    fig, [shifted_ax, unshifted_ax] = plt.subplots(
        2, 1, figsize=figsize, sharex=True, layout='tight'
        )
    # Plot the fitted curve and derivative
    x = np.linspace(time_nodes[0], time_nodes[-1], 600)
    lifetime = ufloat(*data['result']['lifetime'])
    spline_weights = np.array([
        # sorted by key to make sure weight order is correct
        val[0] for key, val in sorted(data['result'].items())
        if key.startswith(f'shifted_weight')
        ])
    fit = spline_weights@bsplines.basis(
        data[f'decay_order'], time_nodes, x, 0
        ).T
    derivative = spline_weights@bsplines.basis(
        data[f'decay_order'], time_nodes, x, 1
        ).T
    shifted_ax.plot(x, fit, '-k')
    unshifted_ax.plot(
        x, lifetime.nominal_value*derivative, '--k',
        label=r"$\tau\frac{\mathrm{d}}{\mathrm{d}t}I_\mathrm{shifted}$")
    unshifted_ax.legend()

    # Plot the data points
    for ax, curve_name in zip([shifted_ax, unshifted_ax], ['shifted', 'unshifted']):
        ax.errorbar(
            time_points,
            data[f'{curve_name}_data'][0],
            xerr=time_point_errs,
            yerr=data[f'{curve_name}_data'][1],
            linestyle='',
            marker='',
            capsize=3,
            color='k'
                )
        ax.set_ylabel(rf"$I_\mathrm{{{curve_name}}} / I_\mathrm{{ref}}$",
                      rotation=0, ha='center', va='bottom')
        ax.get_yaxis().set_label_coords(0, 1)

    # Make good looking axes
    adjust_spines(shifted_ax, ['left'])
    unshifted_ax.set_xlabel(f"{data['x_quantity']} / {data['x_unit']}")
    unshifted_ax.spines.bottom.set_bounds(time_nodes[0], time_nodes[-1])
    adjust_spines(unshifted_ax, ['left', 'bottom'])

    return fig

def serialize_figure_content(fig):
    # Note: This is only intended to work with these specific figures.
    content = []
    for ax in fig.axes[:2]: # data and curves, same for singles and coinc
        elements = ax.get_children()
        content.append({
            'curve': [elements[0].get_xdata().tolist(),
                      elements[0].get_ydata().tolist()],
            'datapoints': [elements[1].get_xdata().tolist(),
                           elements[1].get_ydata().tolist()],
            'xerrors': get_errors_from_intervals(elements[2].get_segments(), axis=0),
            'yerrors': get_errors_from_intervals(elements[3].get_segments(), axis=1)
            })
    try: # derivative fit, only for singles
        ax = fig.axes[2]
    except IndexError:
        pass # fig was coinc
    else:
        elements = ax.get_children()
        content.append({
            'difference' : [elements[0].get_xdata().tolist(),
                            elements[0].get_ydata().tolist()],
            'derivative' : [elements[1].get_xdata().tolist(),
                            elements[1].get_ydata().tolist()]
            })
    return content

def get_errors_from_intervals(intervals, axis) -> list:
    """ calculate symmetric errors from confidence intervals

        intervals as list[np.array([[xmin, ymin], [xmax, ymax]])]
        axis can be 0 (x) or 1 (y)
    """
    return [(interval[1, axis] - interval[0, axis])/2 for interval in intervals]


def adjust_spines(ax, visible_spines):
    """
    adapted from
    https://matplotlib.org/stable/gallery/spines/spines_dropped.html
    """
    ax.label_outer(remove_inner_ticks=True)
    ax.grid(color='0.9')
    ax.margins(0.01)

    for loc, spine in ax.spines.items():
        if loc in visible_spines:
            spine.set_position(('outward', 10))  # outward by 10 points
        else:
            spine.set_visible(False)


if __name__ == '__main__':
    main()
