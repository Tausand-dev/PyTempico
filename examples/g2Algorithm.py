# -*- coding: utf-8 -*-
"""g2Algorithm

    Pure math/signal-processing core for the real-time HBT
    (Hanbury Brown and Twiss) experiment using Tausand Tempico devices
    (TP1204 and TP1004) -- Second-order correlation function g²(τ).

    This module contains ONLY the histogram accumulation and g²(τ)
    normalization logic. Everything related to device communication,
    channel configuration, and acquisition lives in g2Example.py.

    g²(τ) normalization -- average of all non-empty histogram bins:
        baseline = mean( C(τ) for all non-empty bins )
        g²(τ)   = C(τ) / baseline

    This normalization is correct when START and STOP come from the same
    TDC (n_stops ≈ n_starts). The classic formula r·r·T·dt produces a
    baseline of the order 10⁻⁵, inflating g²(τ) into the thousands.

    Negative tau delays (start arrives after the stop) are native to the
    TP1204 in mode 1 or mode 2 and do not require an external delay line.
    The TP1004 only delivers positive tau values; its histogram window is
    asymmetric: [0, +window_ns].

    REQUIRED LIBRARIES (install before running):
        pip install numpy

    | @author: Miguelangel García Castilo, Tausand Electronics
    |  mgarcia@tausand.com 
    | https://www.tausand.com
"""

# ── Imports ────────────────────────────────────────────────────────────────
import numpy as np


# ── G2Computer ─────────────────────────────────────────────────────────────
class G2Computer:
    """
    Stateful histogram accumulator and g²(τ) normalizer.

    Owns the bin edges, bin centres, and accumulated counts array.
    Receives raw tau values [ns] via accumulate() and returns the
    normalized g²(τ) curve via compute_g2().

    No device, no Qt, no Tempico specifics -- pure numpy math only.

    Parameters
    ----------
    bin_ns : float
        Histogram bin width in nanoseconds.
    window_ns : float
        Half-width of the histogram window in nanoseconds.
        - TP1204: histogram spans [-window_ns, +window_ns].
        - TP1004: histogram spans [0, +window_ns] (positive tau only).
    n_runs : int
        Number of runs per acquisition batch (used to select batched mode).
    positive_only : bool, optional
        Set to True for the TP1004, which does not produce negative tau
        values. When True the histogram spans [0, +window_ns] instead of
        the symmetric [-window_ns, +window_ns] (default: False).
    """

    def __init__(self, bin_ns, window_ns, n_runs, positive_only=False):
        self.bin_ns        = bin_ns
        self.window_ns     = window_ns
        self.positive_only = positive_only

        # -- Build histogram edges -------------------------------------------
        # Edges are shifted by half a bin so bin centres fall on multiples of
        # bin_ns. For the TP1204 the centre at tau = 0 is always present.
        # For the TP1004 the leftmost centre is at +bin_ns/2.
        n_half   = max(int(np.ceil(window_ns / bin_ns)), 1)
        half_bin = bin_ns / 2.0

        if positive_only:
            # Asymmetric window: [0, +window_ns]
            tau_min = 0.0
        else:
            # Symmetric window: [-window_ns, +window_ns]
            tau_min = -window_ns

        edges = np.arange(0, n_half + 1) * bin_ns - half_bin + tau_min + half_bin
        # Ensure the first edge starts at tau_min
        edges = np.concatenate([[tau_min], edges[edges > tau_min]])
        # Build uniform edges spanning the full window
        n_bins_full = int(np.round((window_ns - tau_min) / bin_ns))
        if positive_only:
            edges = np.linspace(0.0, window_ns, n_bins_full + 1)
        else:
            edges = np.linspace(-window_ns, window_ns, 2 * n_half + 1)

        self.edges   = edges
        self.n_bins  = len(self.edges) - 1
        self.centres = 0.5 * (self.edges[:-1] + self.edges[1:])
        self.counts  = np.zeros(self.n_bins, dtype=np.float64)

        # Batched mode is used when n_runs > 50 (ThreadStartStop pattern)
        self.isBatched = (n_runs > 50)

        # -- Event counters (updated by g2Example.py after each raw event) ---
        self.n_starts     = 0
        self.n_stops      = 0
        self.total_events = 0

    # ── accumulate ────────────────────────────────────────────────────────
    def accumulate(self, taus_ns):
        """
        Add tau delays [ns] to the accumulated histogram.

        Uses floor((tau - tau_min) / bin_ns) to map the measurement window
        to indices [0, n_bins-1]. Values outside the window are silently
        discarded.

        Parameters
        ----------
        taus_ns : array-like
            Tau delay values in nanoseconds. May include negative values for
            the TP1204 (positive_only=False); negative values are silently
            discarded for the TP1004 (positive_only=True).
        """
        arr      = np.asarray(taus_ns, dtype=np.float64)
        tau_min  = 0.0 if self.positive_only else -self.window_ns
        tau_max  = self.window_ns

        # Keep only tau values inside the measurement window
        valid = (arr >= tau_min) & (arr <= tau_max)
        arr   = arr[valid]
        if len(arr) == 0:
            return

        idx = np.floor((arr - tau_min) / self.bin_ns).astype(int)
        idx = np.clip(idx, 0, self.n_bins - 1)
        np.add.at(self.counts, idx, 1)

    # ── compute_g2 ────────────────────────────────────────────────────────
    def compute_g2(self, t_elapsed):
        """
        Normalize the histogram to obtain g²(τ).

        The TP1204 and TP1004 measure start→stop with a single channel:
        each start produces exactly one stop, so n_stops ≈ n_starts.
        The classic formula baseline = r_s · r_p · T · dt gives an
        extremely small baseline (~10⁻⁵ at ~700 cps / 0.1 ns bin),
        inflating g²(τ) into the thousands.

        The correct normalization divides by the average value of all
        non-empty histogram bins, where the correlation is flat (random-
        coincidence background):

            baseline = mean( counts[ all non-empty bins ] )
            g²(τ)   = counts(τ) / baseline

        If fewer than 2 non-empty bins are present, a fallback baseline of
        1.0 is used to avoid division by zero.

        Parameters
        ----------
        t_elapsed : float
            Wall-clock time elapsed since acquisition started, in seconds.

        Returns
        -------
        g2 : ndarray, shape (n_bins,)
            Normalized second-order correlation function.
        rate_s : float
            Start rate in counts/s.
        rate_p : float
            Stop rate in counts/s.
        baseline : float
            Mean counts per bin used for normalization.
        """
        g2     = np.zeros(self.n_bins, dtype=np.float64)
        rate_s = self.n_starts / t_elapsed if t_elapsed > 0 else 0.0
        rate_p = self.n_stops  / t_elapsed if t_elapsed > 0 else 0.0

        if self.n_stops < 10:
            return g2, rate_s, rate_p, 0.0

        # Baseline = mean of ALL non-empty bins
        all_nonzero = self.counts[self.counts > 0]
        if len(all_nonzero) >= 2:
            baseline = float(np.mean(all_nonzero))
        else:
            baseline = 1.0

        if baseline > 0:
            g2 = self.counts / baseline

        return g2, rate_s, rate_p, baseline