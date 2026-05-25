# -*- coding: utf-8 -*-
"""MultipleTauCorrelator

    Created on [date]

    Multi-tau autocorrelation algorithm for Fluorescence Correlation
    Spectroscopy (FCS). Computes the normalized autocorrelation function
    G(tau) from a stream of intensity values (photon counts per bin) using
    the multi-tau scheme, which combines linear spacing at short lag times
    with logarithmic spacing at long lag times.

    Instructions:
        - Import this module and instantiate ``MultiTauCorrelator`` with
          the desired ``tau_0``, ``num_levels``, and ``m`` parameters.
        - Feed intensity bins one at a time using ``process_datum(value)``,
          where ``value`` is the photon count in each time bin.
        - After feeding all data, call ``get_correlation_curve()`` to
          retrieve the arrays of lag times and G(tau) values.
        - The lag times are returned in the same units as ``tau_0``.
          If ``tau_0`` is given in picoseconds, divide by 1e12 to convert
          to seconds.

    Example usage::

        correlator = MultiTauCorrelator(tau_0=100e3, num_levels=16, m=16)
        for photon_count in intensity_series:
            correlator.process_datum(photon_count)
        taus, g = correlator.get_correlation_curve()

    | @author: Miguelangel García Castillo, Tausand Electronics
    | mgarcia@tausand.com
    | https://www.tausand.com
"""

import numpy as np

# --- MULTI-TAU CORRELATOR CLASS ---
class MultiTauCorrelator:
    """
    Multi-tau autocorrelation algorithm for Fluorescence Correlation Spectroscopy (FCS).

    Computes the normalized autocorrelation function G(tau) from a stream of
    intensity values (photon counts per bin) using the multi-tau scheme.
    This scheme uses linearly spaced channels at the base level and
    logarithmically spaced channels at higher levels, allowing efficient
    computation over many decades of lag time.

    The normalization used is:

        G(tau) = <I(t) * I(t + tau)> / <I(t)>^2

    where I(t) is the photon count in bin t.

    Parameters
    ----------
    tau_0 : float, optional
        Base lag time (duration of the smallest bin), in any consistent time
        unit (e.g. picoseconds). Default is 1.0.
    num_levels : int, optional
        Number of levels in the multi-tau hierarchy. Each level k covers lag
        times up to ``m * 2^k * tau_0``. Default is 16.
    m : int, optional
        Number of channels (shift register length) per level. Must be a
        positive even integer. The first level uses all m channels with
        linear spacing. Higher levels use the upper m//2 channels to avoid
        overlap with the previous level. Default is 16.

    Attributes
    ----------
    shift_registers : list of numpy.ndarray
        Circular buffers of length m for each level, holding the m most
        recent binned intensity values at that level's time resolution.
    A : list of numpy.ndarray
        Accumulated cross-products for each channel at each level.
        Used as the numerator of G(tau).
    M_del : list of numpy.ndarray
        Accumulated sum of delayed (older) intensity values for each channel
        at each level. Used as part of the denominator of G(tau).
    M_dir : numpy.ndarray
        Accumulated sum of direct (current) intensity values for each level.
        Used as part of the denominator of G(tau).
    n_bins : numpy.ndarray of int
        Number of bins processed at each level.
    z_buffer : numpy.ndarray
        Accumulation buffer used to combine pairs of bins when passing data
        from level k to level k+1.

    Examples
    --------
    >>> correlator = MultiTauCorrelator(tau_0=100e3, num_levels=16, m=16)
    >>> for photon_count in intensity_series:
    ...     correlator.process_datum(photon_count)
    >>> taus, g = correlator.get_correlation_curve()
    """
    def __init__(self, tau_0=1.0, num_levels=16, m=16):
        # Store the base lag time; all tau values will be multiples of this
        self.tau_0 = tau_0
        # Total number of levels in the multi-tau hierarchy
        self.num_levels = num_levels
        # Number of channels (shift register slots) per level
        self.m = m

        # One shift register per level: holds the m most recent intensity
        # values at that level's time resolution. Acts as a circular buffer.
        self.shift_registers = [np.zeros(m) for _ in range(num_levels)]

        # A[k][i]: accumulated cross-product between current bin and the bin
        # that arrived i+1 steps ago at level k. Numerator of G(tau).
        self.A = [np.zeros(m) for _ in range(num_levels)]

        # M_del[k][i]: accumulated sum of delayed intensity values at channel i,
        # level k. Tracks the mean of the older (delayed) signal. Part of denominator.
        self.M_del = [np.zeros(m) for _ in range(num_levels)]

        # M_dir[k]: accumulated sum of direct (current) intensity at level k.
        # Tracks the mean of the newer (direct) signal. Part of denominator.
        self.M_dir = np.zeros(num_levels)

        # n_bins[k]: total number of bins processed at level k.
        # Used for normalization and to determine when a level has enough data.
        self.n_bins = np.zeros(num_levels, dtype=int)

        # z_buffer[k]: temporary accumulator that sums pairs of bins from
        # level k-1 before passing them up to level k. Implements the
        # factor-of-2 coarsening between levels.
        self.z_buffer = np.zeros(num_levels)

    def process_datum(self, value):
        """
        Feed a single intensity bin into the correlator.

        This method triggers the recursive multi-tau update starting at
        level 0. Each call corresponds to one time bin of duration ``tau_0``.

        Parameters
        ----------
        value : float
            Photon count (or intensity) for the current bin. Must be
            non-negative.

        Notes
        -----
        Every two calls to this method at level k cause one new value to be
        passed to level k+1 (with the two values summed), implementing the
        factor-of-2 coarsening between levels.
        """
        # Entry point: always start the recursive update at level 0
        self._run_level(0, value)

    def _run_level(self, k, z_k):
        """
        Perform the multi-tau update at level k with input value z_k.

        Updates the accumulator arrays A, M_del, and M_dir for level k,
        advances the shift register, and recursively propagates a coarsened
        value to level k+1 every two bins.

        Parameters
        ----------
        k : int
            Current level index (0-based). Level 0 operates at the base
            time resolution ``tau_0``; level k operates at resolution
            ``2^k * tau_0``.
        z_k : float
            Intensity value (photon count) for the current bin at level k.

        Notes
        -----
        The update equations at each level are:

            A[k][i]     += z_k * shift_registers[k][i]   for all i
            M_del[k][i] += shift_registers[k][i]          for all i
            M_dir[k]    += z_k

        After updating, the shift register is rolled by one position and
        z_k is inserted at index 0 (most recent position).

        Every second call (when n_bins[k] is even), the accumulated
        z_buffer[k+1] is passed to _run_level(k+1) and reset to zero.
        """
        # Cross-product accumulation: multiply current bin z_k by each of the
        # m delayed values in the shift register. This is the core FCS
        # correlation operation: <I(t) * I(t + tau)> for all m lag channels.
        self.A[k] += z_k * self.shift_registers[k]

        # Accumulate the delayed values for normalization (denominator term).
        # M_del[k][i] will hold the sum of all values that have passed through
        # channel i, representing <I(t + tau)> for each lag.
        self.M_del[k] += self.shift_registers[k]

        # Accumulate the direct (current) value for normalization.
        # M_dir[k] will hold the total sum of all input values at this level,
        # representing <I(t)>.
        self.M_dir[k] += z_k

        # Count how many bins have been processed at this level
        self.n_bins[k] += 1

        # Advance the circular shift register: roll all values one position
        # to the right (older), then insert z_k at position 0 (most recent).
        # After this, shift_registers[k][i] holds the value from i+1 bins ago.
        self.shift_registers[k] = np.roll(self.shift_registers[k], 1)
        self.shift_registers[k][0] = z_k

        # Coarsening step: accumulate z_k into the buffer for the next level.
        # When two consecutive bins have been accumulated (n_bins[k] is even),
        # their sum is passed up to level k+1 as a single coarser bin.
        # This implements the factor-of-2 time resolution reduction per level.
        if k + 1 < self.num_levels:
            self.z_buffer[k+1] += z_k
            if self.n_bins[k] % 2 == 0:
                # Two bins accumulated: send their sum to the next level
                new_z = self.z_buffer[k+1]
                # Reset buffer for the next pair
                self.z_buffer[k+1] = 0
                # Recursive call: process the coarsened bin at level k+1
                self._run_level(k + 1, new_z)

    def get_correlation_curve(self):
        """
        Compute and return the normalized autocorrelation function G(tau).

        Iterates over all levels and channels, skipping levels with
        insufficient data (fewer than m bins processed) and channels
        with zero delayed accumulator (to avoid division by zero).

        At level 0, all m channels are included (linear spacing).
        At levels 1 and above, only the upper m//2 channels are included
        (indices m//2 to m-1) to avoid overlap with the previous level,
        following the standard multi-tau scheme.

        The lag time for channel i at level k is:

            tau = (i + 1) * 2^k * tau_0

        The normalized correlation value is:

            G(tau) = (A[k][i] * n_bins[k]) / (M_dir[k] * M_del[k][i])

        Returns
        -------
        taus : numpy.ndarray
            Array of lag times in the same units as ``tau_0``.
        g_vals : numpy.ndarray
            Array of normalized autocorrelation values G(tau) corresponding
            to each lag time in ``taus``.

        Notes
        -----
        If fewer than ``m`` bins have been processed at a given level,
        that level is skipped and contributes no points to the output.
        This typically affects the highest levels early in an acquisition.
        """
        taus, g_vals = [], []

        for k in range(self.num_levels):
            # Skip levels that have not yet accumulated enough bins to fill
            # all m channels of the shift register. Without this guard,
            # the early channels would be computed from incomplete data.
            if self.n_bins[k] < self.m:
                continue

            # At level 0 use all m channels (linear spacing from tau_0 to m*tau_0).
            # At levels k >= 1 skip the first m//2 channels because those lag
            # times are already covered by the previous level at finer resolution,
            # avoiding duplicate points in the output curve.
            start_idx = 0 if k == 0 else 8

            for i in range(start_idx, self.m):
                m_del = self.M_del[k][i]

                # Skip channels where no delayed data has been accumulated yet,
                # which would cause a division by zero in the normalization.
                if m_del == 0:
                    continue

                # Normalized autocorrelation for channel i at level k:
                #   G(tau) = <I(t)*I(t+tau)> / (<I(t)> * <I(t+tau)>)
                # In accumulated form:
                #   numerator   = A[k][i] (cross-product sum)
                #   denominator = M_dir[k] / n_bins[k]  *  M_del[k][i] / n_bins[k]
                # Rearranging to avoid two divisions:
                #   G = (A[k][i] * n_bins[k]) / (M_dir[k] * M_del[k][i])
                g = (self.A[k][i] * self.n_bins[k]) / (self.M_dir[k] * m_del)

                # Lag time for channel i at level k:
                # channel i corresponds to a delay of (i+1) bins at this level,
                # and each bin at level k has duration 2^k * tau_0.
                tau = (i + 1) * (2**k) * self.tau_0

                taus.append(tau)
                g_vals.append(g)

        return np.array(taus), np.array(g_vals)