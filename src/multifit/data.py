from typing import Self

from math import sqrt
import numpy as np
from numpy.typing import ArrayLike

class Data:
    """Base class for input data."""
    def __init__(self, counts: ArrayLike, bin_edges: ArrayLike, key: str):
        """General constructor for the Spectrum class.

        Arguments:
        counts -- number of events in each bin.
        bin_edges -- bin edges, including the left edge of the first bin
            and the right edge of the last bin.
        key -- a key used when sorting multiple spectra.
        """
        self.bin_edges = np.array(bin_edges)
        self.counts = np.array(counts)
        self.key = key

    @classmethod
    def equal_bins(
            cls, *,
            counts: ArrayLike,
            bin_width: float,
            minimum: float = 0,
            key: str,
            ) -> Self:
        """Construct an instance of cls with equal width bins."""
        # upper_limit must be slightly higher than the maximum value to
        # ensure it gets included in the arange.
        counts = cls.reshape(counts)
        upper_limit = minimum + (len(counts) + 0.01)*bin_width
        bin_edges = np.arange(minimum, upper_limit, bin_width)
        return cls(counts=counts, bin_edges=bin_edges, key=key)

    def __lt__(self, other):
        return self.key < other.key

    @classmethod
    def reshape(cls, counts):
        raise NotImplementedError(
            "The reshape method should be implemented in the subclasses. "
            "This class is not meant to be used directly."
            )


class Spectrum(Data):
    def __init__(self, *, counts: ArrayLike, bin_edges: ArrayLike, key: str):
        if len(bin_edges) - 1 != len(counts):
            raise ValueError(
                "Could not initialise Spectrum. "
                "bin_edges must have exactly one more value than counts "
                "(the end of the last bin).")
        super().__init__(counts, bin_edges, key)

    @classmethod
    def reshape(cls, counts):
        return np.ravel(counts)

    def truncate(self, lower_bin_edge, upper_bin_edge, inplace=False):
        """Select a range of the spectrum.

        Keyword arguments:
        lower_bin_edge -- first bin edge to include.
        upper_bin_edge -- last bin edge to include.
        inplace -- if True, modify the current Spectrum and return None,
            if False create and return a new Spectrum.
        """
        idx_min = np.searchsorted(self.bin_edges, lower_bin_edge)
        idx_max = np.searchsorted(self.bin_edges, upper_bin_edge)

        if inplace:
            self.counts = self.counts[idx_min:idx_max]
            self.bin_edges = self.bin_edges[idx_min:idx_max + 1]
            return None
        else:
            return type(self)(
                counts=self.counts[idx_min:idx_max],
                bin_edges=self.bin_edges[idx_min:idx_max + 1],
                key=self.key)


class CoincidenceMatrix(Data):
    def __init__(self, *, counts: ArrayLike, bin_edges: ArrayLike, key: str):
        dim = len(bin_edges) - 1
        counts = np.array(counts)
        if counts.shape != (dim, dim):
            raise ValueError(
                "Could not initialise CoincidenceMatrix. "
                "counts must be shapable into a square matrix of "
                "dimention len(bin_edges) - 1."
                )
        super().__init__(counts, bin_edges, key)

    @classmethod
    def reshape(cls, counts: ArrayLike):
        dim = sqrt(counts.size)
        if dim%1:
            raise ValueError(
                "number of counts is not a square."
                f"{int(dim)**2 = }, {counts.size = }"
                )
        dim = int(dim)
        return np.reshape(counts, (dim, dim))

    def gate(self, lower: float, upper: float) -> Spectrum:
        """Return a Spectrum by gating on the coincidence matrix.

        Arguments:
        lower -- lower value of the gate
        upper -- upper value of the gate
        axis -- axis on which to apply the gate.
        """
        idx_min = np.searchsorted(self.bin_edges, lower)
        idx_max = np.searchsorted(self.bin_edges, upper)

        projection = self.counts[:, idx_min:idx_max].sum(axis=1)
        return Spectrum(
            counts = projection,
            bin_edges=self.bin_edges,
            key=self.key
            )
