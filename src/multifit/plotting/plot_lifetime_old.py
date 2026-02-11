"""plot-lifetime

Usage:
    plot-lifetime expects the output from fit-lifetime as stdin.
    e.g with pipe:
        fit-lifetime (argumenrs ...) | plot-lifetime
    or with redirect:
        plot-lifetime < <fit-lifetime output>

Options:
    -h --help       Show this help screen and exit.
    -v              Print lifetime value and uncertainty
"""

import json
import sys

from attrs import define
from matplotlib import pyplot as plt
import numpy as np
from numpy.typing import NDArray

from ..dcm2 import bsplines

@define
class Something:
    what: str
    points: NDArray
    point_errors: NDArray
    order: int
    weights: NDArray
    # weight_errors: NDArray  # not necessary

def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        print(__doc__)
        sys.exit()

    data = json.load(sys.stdin)
    try:
        time_nodes = np.array(data['time_nodes'])
        time_points = np.array(data['times'])
        time_point_errs = np.array(data['time_errs'])
    except KeyError:
        time_nodes = np.array(data['NODES'])/data['speed']
        time_points = np.array(data['DISTANCES'])/data['speed']
        time_point_errs = np.array(data['DISTANCE_ERRS'])/data['speed']
    include_feeding = 'feeder' in data['argv']
    [lifetime, uncertainty] = data['result']['lifetime']

    if include_feeding:
        decay = Something(
            'decay',
            np.array(data['decay_data'][0]),
            np.array(data['decay_data'][1]),
            data['decay_order'],
            np.array([
                val[0] for key, val in sorted(data['result'].items())
                if key.startswith('decay_weight')
                ])
            )
        feeder = Something(
            'feeder',
            np.array(data['feeder_data'][0]),
            np.array(data['feeder_data'][1]),
            data['feeder_order'],
            np.array([
                val[0] for key, val in sorted(data['result'].items())
                if key.startswith('feeder_weight')
                ])
            )
        things_to_plot = [feeder, decay]
        axes = [None, None]
        fig, (axes[0], axes[1], derivative_ax, lifetime_ax) = plt.subplots(
            4, sharex=True
            )
    else:
        shifted = Something(
            'shifted',
            np.array(data['shifted_data'][0]),
            np.array(data['shifted_data'][1]),
            data['decay_order'],
            a := np.array([
                val[0] for key,val in sorted(data['result'].items())
                if key.startswith('shifted_weight')
                ])
            )
        unshifted = Something(
            'unshifted',
            np.array(data['unshifted_data'][0]),
            np.array(data['unshifted_data'][1]),
            data['decay_order'],
            np.full([len(a)], np.nan)
#            np.array([
#                val[0] for key,val in data['result'].items()
#                if key.startswith('unshifted_weight')
#                ])
            )
        things_to_plot = [shifted, unshifted]
        axes = [None, None]
        fig, (axes[0], axes[1], lifetime_ax) = plt.subplots(3, sharex=True)

    x = np.linspace(time_nodes[0], time_nodes[-1], 1000)
    for ax, thing in zip(axes, things_to_plot):
        fitted_curve = thing.weights@bsplines.basis(
            thing.order, time_nodes, x, 0).T
        fitted_derivative = thing.weights@bsplines.basis(
            thing.order, time_nodes, x, 1).T

        ax.set_ylabel('$Q$')
        ax.vlines(x=time_nodes, ymin=0, ymax=1, linestyle='--', color='gray')
        ax.plot(x, fitted_curve, label='$Q(t)$')
        ax.plot(  # If using Bsplines
            bsplines.control_points(thing.order, inner_knots=time_nodes),
            thing.weights,
            'o:', c='.7', zorder=1
            )
        ax.errorbar(
            time_points, thing.points,
            xerr=time_point_errs, yerr=thing.point_errors,
            label='data', ls='', marker='.'
            )

        match thing.what:
            case 'feeder':  # Derivative is proportional to difference
                difference = data['feeding_coeff'][0]*fitted_curve
            case 'decay':
                difference -= fitted_curve
            case 'shifted':
                derivative = fitted_derivative
                point_derivative = thing.weights@bsplines.basis(
                    thing.order, time_nodes, time_points, 1).T
            case 'unshifted':  # Derivative of s is proportional to u
                ax.plot(
                    x,
                    lifetime*derivative,
                    label=r'$\tau\frac{\mathrm{d}}{\mathrm{d}t}'
                          r'I_\mathrm{shifted}(t)$'
                    )

        ax.legend()

    if include_feeding:
        # the current loop variables are for the decay
        derivative_ax.plot(
            x,
            lifetime*fitted_derivative,
            label=r'$\tau\mathrm{d}Q/\mathrm{d}t$'
            )
        derivative_ax.plot(
            x,
            difference,
            label=r"$\alpha Q_k(t) - Q_i(t)$"
            )
        derivative_ax.legend()

    if not data['success']:
        axes[0].set_title("WARNING: Invalid fit")

    lifetime_ax.set_xlabel(f"{data['x_quantity']} / {data['x_unit']}")
    if include_feeding:
        lifetime_ax.plot(
            x[:-1],
            difference[:-1]/fitted_derivative[:-1],
            color='tab:orange'
            )
    else:
        lifetime_ax.plot(
            time_points,
            thing.points/point_derivative,
            '.:',
            color='tab:orange'
            )
    if uncertainty:
        lifetime_ax.axhspan(lifetime - uncertainty,
                            lifetime + uncertainty,
                            alpha=0.2)
        lifetime_ax.set_ylim((lifetime - uncertainty*3,
                              lifetime + uncertainty*3
                              ))

    lifetime_ax.axhline(lifetime)

    if '-v' in sys.argv:
        print(f"χ²/ndf = {data['chi2/ndf']:.3f}")
        print(f"τ = {lifetime:.3f} ± {uncertainty:.3f} ps")
        print(f"t½ = {lifetime*np.log(2):.3f} ± {uncertainty*np.log(2):.3f} ps")

    plt.show()


