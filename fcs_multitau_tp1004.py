# -*- coding: utf-8 -*-
"""fcs_multitau_tp1004.py

Fluorescence Correlation Spectroscopy (FCS) using a Tausand Tempico TP1004
device via pyTempico, with a Multi-tau autocorrelation algorithm.

The user configures tau_0, tau_max, acquisition time, and a photon target.
The number of correlator levels is computed automatically to cover the
requested range, rounded up to the nearest power of 2.

Hardware setup
--------------
- TP1004 configured on Channel 1, Mode 2 (125 ns - 4 ms range).
- Start input : periodic trigger signal (~100 Hz recommended).
- Stop input  : APD detector output. Up to 5 stops per start cycle.

Data format returned by measure()
----------------------------------
    [[ch, run, start_s, stop_ps1, ..., stop_psN], ...]

  stop_psK  = absolute start->stop time in picoseconds for stop K.
  delta_t between consecutive stops is obtained by subtraction.

Cycle splicing (Section 1 of the algorithm document)
------------------------------------------------------
stop_ps1 of a new run is the boundary photon shared with the last stop of
the previous run and is DISCARDED to avoid double-counting.

Algorithm reference
-------------------
Garcia Castillo, M. "Fluorescence Correlation Spectroscopy using Tausand
Tempico devices." Tausand Electronics, April 2026.

Dependencies
------------
    pip install pyTempico numpy matplotlib

| @author: Miguelangel Garcia Castillo, Tausand Electronics
| https://www.tausand.com
"""

import math
import sys
import time
import threading
import queue

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import pyTempico

# =============================================================================
# HARDWARE CONSTANTS  (TP1004 mode 2 limits)
# =============================================================================

TAU_MIN_HARDWARE_S = 125e-9   # Smallest measurable interval in mode 2 (125 ns)
TAU_MAX_HARDWARE_S = 4e-3     # Largest  measurable interval in mode 2 (4 ms)
CHANNELS_L1        = 16       # Channels in level 1 (highest resolution)
CHANNELS_LK        = 8        # Channels in levels k > 1
NUMBER_OF_STOPS    = 2        # Stop inputs used per start cycle (1-5)
NUMBER_OF_RUNS     = 100      # Runs collected per measure() call (1-1000)
PLOT_INTERVAL_MS   = 1000     # Live plot refresh interval in milliseconds


# =============================================================================
# LEVEL CALCULATOR
# =============================================================================

def compute_num_levels(tau0_s: float, tau_max_s: float) -> tuple:
    """
    Compute the minimum number of correlator levels needed to cover tau_max,
    then round up to the nearest power of 2.

    The last channel of each level covers:
      Level 1  : tau_end = CHANNELS_L1 * tau0
      Level k>1: tau_end = (2^(k+2) + CHANNELS_LK * 2^(k-1)) * tau0

    Parameters
    ----------
    tau0_s    : float -- base bin width chosen by the user (seconds)
    tau_max_s : float -- maximum delay time requested (seconds)

    Returns
    -------
    num_levels  : int   -- number of levels (power of 2, >= 1)
    tau_covered : float -- actual maximum tau covered (seconds)
    """
    # Level 1
    tau_end = CHANNELS_L1 * tau0_s
    if tau_end >= tau_max_s:
        return 1, tau_end

    # Levels k > 1
    k = 2
    while True:
        tau_end = (2 ** (k + 2) + CHANNELS_LK * 2 ** (k - 1)) * tau0_s
        if tau_end >= tau_max_s:
            num_levels = 2 ** math.ceil(math.log2(k))
            # Recalculate tau_end for the rounded-up level count
            tau_end = (2 ** (num_levels + 2) +
                       CHANNELS_LK * 2 ** (num_levels - 1)) * tau0_s
            return num_levels, tau_end
        k += 1


# =============================================================================
# USER CONFIGURATION DIALOG
# =============================================================================

def get_user_parameters() -> tuple:
    """
    Interactive prompt for all acquisition parameters.

    Asks for:
      - tau_0    : base bin width (>= 125 ns hardware limit)
      - tau_max  : maximum delay time to compute (> tau_0, <= 4 ms)
      - acq_time : total acquisition time in seconds
      - photon_target : desired photon count (0 = no target)
      - port     : serial port of the TP1004

    Returns
    -------
    tau0_s         : float
    tau_max_s      : float
    acquisition_s  : float
    photon_target  : int   (0 means time-only stop condition)
    port           : str
    """
    print("=" * 62)
    print("  FCS Multi-tau Correlator  -  TP1004 Configuration")
    print("=" * 62)

    # ── tau_0 (base bin width) ────────────────────────────────────────────────
    print(f"\n  tau_0 is the base bin width of the correlator.")
    print(f"  Hardware minimum in mode 2: {TAU_MIN_HARDWARE_S*1e9:.0f} ns")
    print(f"  Larger tau_0 shifts all delay times proportionally.")
    while True:
        try:
            val = input(
                f"  Enter tau_0 in nanoseconds "
                f"[min = {TAU_MIN_HARDWARE_S*1e9:.0f} ns]: "
            ).strip()
            tau0_s = float(val) * 1e-9
            if tau0_s < TAU_MIN_HARDWARE_S:
                print(f"  [!] tau_0 cannot be less than "
                      f"{TAU_MIN_HARDWARE_S*1e9:.0f} ns (hardware limit).")
            elif tau0_s >= TAU_MAX_HARDWARE_S:
                print(f"  [!] tau_0 must be less than "
                      f"{TAU_MAX_HARDWARE_S*1e6:.0f} ms.")
            else:
                break
        except ValueError:
            print("  [!] Please enter a valid number.")

    # ── tau_max ───────────────────────────────────────────────────────────────
    print(f"\n  tau_max is the longest delay time the ACF will cover.")
    while True:
        try:
            val = input(
                f"  Enter tau_max in microseconds "
                f"[min > {tau0_s*1e6:.3f} us, "
                f"max = {TAU_MAX_HARDWARE_S*1e6:.0f} us]: "
            ).strip()
            tau_max_s = float(val) * 1e-6
            if tau_max_s <= tau0_s:
                print("  [!] tau_max must be greater than tau_0.")
            elif tau_max_s > TAU_MAX_HARDWARE_S:
                print(f"  [!] tau_max cannot exceed "
                      f"{TAU_MAX_HARDWARE_S*1e6:.0f} us (hardware limit).")
            else:
                break
        except ValueError:
            print("  [!] Please enter a valid number.")

    # ── Acquisition time ──────────────────────────────────────────────────────
    print(f"\n  The acquisition will stop when EITHER the time limit OR")
    print(f"  the photon target is reached (whichever comes first).")
    while True:
        try:
            val = input("  Enter acquisition time in seconds [e.g. 30]: ").strip()
            acquisition_s = float(val)
            if acquisition_s <= 0:
                print("  [!] Acquisition time must be positive.")
            else:
                break
        except ValueError:
            print("  [!] Please enter a valid number.")

    # ── Photon target ─────────────────────────────────────────────────────────
    print(f"\n  Photon target: acquisition also stops when this many photons")
    print(f"  have been detected. Enter 0 to use time limit only.")
    while True:
        try:
            val = input("  Enter photon target [e.g. 1000000, or 0 to skip]: ").strip()
            photon_target = int(float(val))
            if photon_target < 0:
                print("  [!] Photon target must be >= 0.")
            else:
                break
        except ValueError:
            print("  [!] Please enter a valid integer.")

    # ── COM port ──────────────────────────────────────────────────────────────
    port = input("\n  Enter COM port [e.g. COM5]: ").strip()
    if not port:
        port = "COM5"

    # ── Summary ───────────────────────────────────────────────────────────────
    num_levels, tau_covered = compute_num_levels(tau0_s, tau_max_s)

    print("\n" + "-" * 62)
    print("  Correlator configuration summary")
    print("-" * 62)
    print(f"  tau_0 (base bin)      : {tau0_s*1e9:.1f} ns")
    print(f"  tau_max requested     : {tau_max_s*1e6:.3f} us")
    print(f"  Number of levels      : {num_levels}  "
          f"(next power of 2 >= required)")
    print(f"  tau actually covered  : {tau_covered*1e6:.3f} us")
    print(f"  Acquisition time      : {acquisition_s:.1f} s")
    if photon_target > 0:
        print(f"  Photon target         : {photon_target:,}")
    else:
        print(f"  Photon target         : (none - time limit only)")
    print(f"  COM port              : {port}")
    print("-" * 62)

    confirm = input("\n  Proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  Aborted by user.")
        sys.exit(0)

    return tau0_s, tau_max_s, acquisition_s, photon_target, port


# =============================================================================
# MULTI-TAU CORRELATOR
# =============================================================================

class MultiTauCorrelator:
    """
    Online multi-tau autocorrelator.

    Each level k contains:
      - A circular buffer (shift register) of size n_ch[k].
      - A summing/counter buffer for propagation to the next level.
      - corr_accum[k][i]  Sigma n_k(j) * n_k(j-i)    (numerator, Eq. 3)
      - delay_mon[k][i]   Sigma n_k(j-i)              (delay monitor, Mdel)
      - direct_mon[k]     Sigma n_k(j)                (direct monitor, Mdir)
    """

    def __init__(self, tau0: float, num_levels: int):
        self.tau0       = tau0
        self.num_levels = num_levels
        self.n_ch       = [CHANNELS_L1] + [CHANNELS_LK] * (num_levels - 1)

        # Circular buffer state per level
        self.sr   = [np.zeros(nc, dtype=np.float64) for nc in self.n_ch]
        self.head = [0] * num_levels

        # Summing / counter buffer between adjacent levels
        self.adder   = [0.0] * num_levels
        self.counter = [0]   * num_levels

        # Accumulators per level
        self.corr_accum = [np.zeros(nc, dtype=np.float64) for nc in self.n_ch]
        self.delay_mon  = [np.zeros(nc, dtype=np.float64) for nc in self.n_ch]
        self.direct_mon = [0.0] * num_levels
        self.n_updates  = [0]   * num_levels

        # Input Accumulator state (Section 4)
        self.ia_bin   = -1
        self.ia_count = 0.0

        # Pre-build the tau axis (Equations 4 and 5)
        self.tau_axis = self._build_tau_axis()

    # ── tau axis ─────────────────────────────────────────────────────────────

    def _build_tau_axis(self) -> np.ndarray:
        taus = []
        for k in range(1, self.num_levels + 1):
            nc = self.n_ch[k - 1]
            for i in range(1, nc + 1):
                if k == 1:
                    taus.append(i * self.tau0)
                else:
                    taus.append(
                        (2 ** (k + 2) + i * 2 ** (k - 1)) * self.tau0)
        return np.array(taus)

    # ── Circular buffer helpers (Section 7) ──────────────────────────────────

    def _ordered(self, lv: int) -> np.ndarray:
        """Shift register in chronological order: index 0 = newest."""
        sr, h = self.sr[lv], self.head[lv]
        return np.concatenate((sr[h:], sr[:h]))[::-1]

    def _push(self, lv: int, value: float) -> float:
        """Write value into the oldest slot, advance pointer, return ejected."""
        ejected = self.sr[lv][self.head[lv]]
        self.sr[lv][self.head[lv]] = value
        self.head[lv] = (self.head[lv] + 1) % self.n_ch[lv]
        return ejected

    # ── Core update (Section 3) ───────────────────────────────────────────────

    def _update_level(self, lv: int, value: float):
        ordered = self._ordered(lv)
        self.corr_accum[lv] += value * ordered
        self.delay_mon[lv]  += ordered
        self.direct_mon[lv] += value
        self.n_updates[lv]  += 1
        ejected = self._push(lv, value)
        if lv + 1 < self.num_levels:
            self.adder[lv]   += ejected
            self.counter[lv] += 1
            if self.counter[lv] == 2:
                self._update_level(lv + 1, self.adder[lv])
                self.adder[lv]   = 0.0
                self.counter[lv] = 0

    # ── Zero fast-forward (Section 4) ────────────────────────────────────────

    def _fast_forward_zeros(self, lv: int, n_zeros: int):
        if n_zeros <= 0 or lv >= self.num_levels:
            return
        nc    = self.n_ch[lv]
        steps = min(n_zeros, nc)
        for _ in range(steps):
            ordered = self._ordered(lv)
            self.delay_mon[lv]  += ordered
            self.n_updates[lv]  += 1
            ejected = self._push(lv, 0.0)
            self.adder[lv]   += ejected
            self.counter[lv] += 1
            if self.counter[lv] == 2:
                self._fast_forward_zeros(lv + 1, 1)
                self.adder[lv]   = 0.0
                self.counter[lv] = 0
        remaining = n_zeros - steps
        if remaining > 0:
            self.n_updates[lv] += remaining
            zeros_up = (remaining + self.counter[lv]) // 2
            self.counter[lv]   = (remaining + self.counter[lv]) % 2
            if zeros_up > 0:
                self._fast_forward_zeros(lv + 1, zeros_up)

    # ── Public: feed bin ─────────────────────────────────────────────────────

    def feed_bin(self, bin_index: int, count: float):
        if self.ia_bin < 0:
            self.ia_bin   = bin_index
            self.ia_count = count
            return
        gap = bin_index - self.ia_bin
        if gap == 0:
            self.ia_count += count
            return
        self._update_level(0, self.ia_count)
        if gap > 1:
            self._fast_forward_zeros(0, gap - 1)
        self.ia_bin   = bin_index
        self.ia_count = count

    def flush(self):
        """Force the last retained bin into the cascade (end of acquisition)."""
        if self.ia_bin >= 0 and self.ia_count > 0:
            self._update_level(0, self.ia_count)
            self.ia_bin   = -1
            self.ia_count = 0.0

    # ── Public: compute G(tau) (Equation 3) ──────────────────────────────────

    def get_acf(self) -> tuple:
        G_all = []
        for lv in range(self.num_levels):
            Nk    = max(self.n_updates[lv], 1)
            A     = self.corr_accum[lv]
            Mdir  = self.direct_mon[lv]
            Mdel  = self.delay_mon[lv]
            denom = Mdir * Mdel
            with np.errstate(invalid='ignore', divide='ignore'):
                G_k = np.where(denom > 0, (A * Nk) / denom, np.nan)
            G_all.extend(G_k.tolist())
        return self.tau_axis.copy(), np.array(G_all)

    @property
    def total_photons(self) -> int:
        return self.n_updates[0]


# =============================================================================
# PHOTON STREAM RECONSTRUCTOR  (Sections 1 and 2)
# =============================================================================

class PhotonStreamReconstructor:
    """
    Converts raw TP1004 data rows into a continuous photon arrival-time
    sequence by splicing consecutive measurement runs.

    Row format: [ch, run, start_s, stop_ps1, ..., stop_psN]

    Splicing rule (Section 1):
      stop_ps1 of each new run equals the last stop of the previous run
      (boundary photon) -> DISCARDED to avoid double-counting.
    """

    def __init__(self, tau0: float):
        self.tau0          = tau0
        self.cumulative_t  = 0.0
        self.last_stop_ps  = None
        self.time_array    = []
        self._total_photons = 0

    @property
    def total_photons(self) -> int:
        return self._total_photons

    def process_rows(self, rows: list) -> list:
        new_arrivals = []
        for row in rows:
            stops_ps = row[3:]
            if not stops_ps:
                continue

            if self.last_stop_ps is None:
                # First run: use stop_ps1 as the absolute time origin.
                self.cumulative_t += stops_ps[0] * 1e-12
                new_arrivals.append(self.cumulative_t)
                prev_ps = stops_ps[0]
                for stop_ps in stops_ps[1:]:
                    self.cumulative_t += (stop_ps - prev_ps) * 1e-12
                    new_arrivals.append(self.cumulative_t)
                    prev_ps = stop_ps
            else:
                # Subsequent run: discard stops_ps[0] (boundary photon).
                prev_ps = self.last_stop_ps
                for stop_ps in stops_ps[1:]:
                    self.cumulative_t += (stop_ps - prev_ps) * 1e-12
                    new_arrivals.append(self.cumulative_t)
                    prev_ps = stop_ps

            self.last_stop_ps = stops_ps[-1]

        self.time_array.extend(new_arrivals)
        self._total_photons += len(new_arrivals)
        return new_arrivals


# =============================================================================
# INPUT ACCUMULATOR  (Section 4)
# =============================================================================

class InputAccumulator:
    def __init__(self, correlator: MultiTauCorrelator, tau0: float):
        self.correlator = correlator
        self.tau0       = tau0

    def process_arrivals(self, arrival_times: list):
        for t in arrival_times:
            k = int(t / self.tau0)
            self.correlator.feed_bin(k, 1.0)


# =============================================================================
# ACQUISITION PROGRESS TRACKER
# =============================================================================

class AcquisitionProgress:
    """
    Tracks acquisition progress along TWO independent axes:

    1. Time axis  : elapsed vs. acquisition_s  (uses device clock via
                    my_device.getDateTime() after setDateTime() sync,
                    falls back to time.time() if the device returns -1).

    2. Photon axis: accumulated photons vs. photon_target
                    (0 = no photon target, time axis only).

    The acquisition ends when EITHER condition is satisfied.
    """

    def __init__(self, device, acquisition_s: float, photon_target: int,
                 reconstructor: PhotonStreamReconstructor):
        self.device         = device
        self.acquisition_s  = acquisition_s
        self.photon_target  = photon_target
        self.reconstructor  = reconstructor
        self._t0_hw         = None
        self._t0_wall       = None

    def start(self):
        hw = self.device.getDateTime()
        self._t0_hw   = hw if (hw is not None and hw > 0) else None
        self._t0_wall = time.time()

    # ── Time axis ─────────────────────────────────────────────────────────────

    def elapsed(self) -> float:
        if self._t0_hw is not None:
            hw = self.device.getDateTime()
            if hw is not None and hw > 0:
                return hw - self._t0_hw
        return time.time() - self._t0_wall

    def time_remaining(self) -> float:
        return max(0.0, self.acquisition_s - self.elapsed())

    def time_fraction(self) -> float:
        return min(1.0, self.elapsed() / self.acquisition_s)

    # ── Photon axis ───────────────────────────────────────────────────────────

    def photon_count(self) -> int:
        return self.reconstructor.total_photons

    def photon_remaining(self) -> int:
        if self.photon_target <= 0:
            return -1   # no target
        return max(0, self.photon_target - self.photon_count())

    def photon_fraction(self) -> float:
        if self.photon_target <= 0:
            return 0.0
        return min(1.0, self.photon_count() / self.photon_target)

    # ── Stop condition ────────────────────────────────────────────────────────

    def should_stop(self) -> bool:
        """True when time limit OR photon target has been reached."""
        if self.time_remaining() <= 0:
            return True
        if self.photon_target > 0 and self.photon_remaining() <= 0:
            return True
        return False

    # ── Text bar (console) ────────────────────────────────────────────────────

    def bar(self, width: int = 25) -> str:
        """Return a two-bar progress string for console output."""
        # Time bar
        tf     = self.time_fraction()
        t_fill = int(tf * width)
        t_bar  = '#' * t_fill + '-' * (width - t_fill)
        t_str  = (f"Time  [{t_bar}] {tf*100:5.1f}%  "
                  f"elapsed {self.elapsed():6.1f}s / "
                  f"{self.acquisition_s:.0f}s  "
                  f"(rem {self.time_remaining():5.1f}s)")

        # Photon bar
        n = self.photon_count()
        if self.photon_target > 0:
            pf     = self.photon_fraction()
            p_fill = int(pf * width)
            p_bar  = '#' * p_fill + '-' * (width - p_fill)
            p_str  = (f"Photons [{p_bar}] {pf*100:5.1f}%  "
                      f"{n:>10,} / {self.photon_target:,}  "
                      f"(rem {self.photon_remaining():,})")
        else:
            p_str  = f"Photons {n:>12,}  (no target)"

        return t_str + "   |   " + p_str


# =============================================================================
# PRODUCER – CONSUMER THREADS  (Section 4.1)
# =============================================================================

def producer_thread(device, data_queue, stop_event, reconstructor):
    while not stop_event.is_set():
        try:
            rows = device.measure()
            if rows:
                arrivals = reconstructor.process_rows(rows)
                if arrivals:
                    data_queue.put(arrivals)
        except Exception as e:
            print(f"\n[Producer] {e}")
            time.sleep(0.05)


def consumer_thread(data_queue, accumulator, stop_event):
    while not stop_event.is_set() or not data_queue.empty():
        try:
            arrivals = data_queue.get(timeout=0.1)
            accumulator.process_arrivals(arrivals)
        except queue.Empty:
            continue
        except Exception as e:
            print(f"\n[Consumer] {e}")


def progress_thread(progress: AcquisitionProgress,
                    stop_event: threading.Event,
                    interval_s: float = 1.0):
    """Print dual progress bars to the console every interval_s seconds."""
    while not stop_event.is_set():
        print(f"\r{progress.bar()}  ", end='', flush=True)
        time.sleep(interval_s)
    # Final update after stop
    print(f"\r{progress.bar()}  [DONE]")


# =============================================================================
# LIVE PLOT
# =============================================================================

def live_acf_plot(correlator: MultiTauCorrelator,
                  progress: AcquisitionProgress,
                  stop_event: threading.Event,
                  tau0_s: float,
                  tau_max_s: float):
    """
    Display a live G(tau) curve.
    The title shows BOTH progress axes (time and photons) updated every
    PLOT_INTERVAL_MS milliseconds.
    """
    fig, (ax_acf, ax_prog) = plt.subplots(
        2, 1, figsize=(9, 7),
        gridspec_kw={'height_ratios': [4, 1]}
    )
    fig.subplots_adjust(hspace=0.4)

    # ── ACF subplot ───────────────────────────────────────────────────────────
    ax_acf.set_xscale('log')
    ax_acf.set_xlabel('Delay time tau (s)')
    ax_acf.set_ylabel('G(tau)')
    ax_acf.grid(True, which='both', alpha=0.3)
    line, = ax_acf.plot([], [], 'o-', ms=3, lw=1.2, color='royalblue',
                        label='G(tau)')
    ax_acf.axvline(tau0_s,   color='seagreen', lw=1, ls=':',
                   label=f'tau_0 = {tau0_s*1e9:.0f} ns')
    ax_acf.axvline(tau_max_s, color='tomato',  lw=1, ls='--',
                   label=f'tau_max = {tau_max_s*1e6:.1f} us')
    ax_acf.legend(loc='upper right', fontsize=8)

    # ── Progress subplot (two horizontal bars) ────────────────────────────────
    ax_prog.set_xlim(0, 1)
    ax_prog.set_ylim(-0.5, 1.5)
    ax_prog.axis('off')

    # Time bar
    bar_t_bg = ax_prog.barh(1, 1, color='#e0e0e0', height=0.4, left=0)
    bar_t_fg = ax_prog.barh(1, 0, color='steelblue', height=0.4, left=0)
    txt_t    = ax_prog.text(0.5, 1, '', ha='center', va='center',
                             fontsize=8, color='white', fontweight='bold')
    ax_prog.text(-0.01, 1, 'Time', ha='right', va='center', fontsize=8)

    # Photon bar
    bar_p_bg = ax_prog.barh(0, 1, color='#e0e0e0', height=0.4, left=0)
    bar_p_fg = ax_prog.barh(0, 0, color='darkorange', height=0.4, left=0)
    txt_p    = ax_prog.text(0.5, 0, '', ha='center', va='center',
                             fontsize=8, color='white', fontweight='bold')
    ax_prog.text(-0.01, 0, 'Photons', ha='right', va='center', fontsize=8)

    def update(_frame):
        if stop_event.is_set():
            plt.close(fig)
            return

        # Update ACF curve
        tau, G = correlator.get_acf()
        valid  = np.isfinite(G)
        if valid.any():
            line.set_data(tau[valid], G[valid])
            ax_acf.relim()
            ax_acf.autoscale_view()

        # Update ACF title
        ax_acf.set_title(
            f'FCS - Multi-tau ACF (live)  |  '
            f'photons: {progress.photon_count():,}  |  '
            f'elapsed: {progress.elapsed():.1f}s  |  '
            f'remaining: {progress.time_remaining():.1f}s'
        )

        # Update time bar
        tf = progress.time_fraction()
        bar_t_fg[0].set_width(tf)
        txt_t.set_text(
            f"{tf*100:.1f}%  {progress.elapsed():.1f}s / "
            f"{progress.acquisition_s:.0f}s  "
            f"(rem {progress.time_remaining():.1f}s)"
        )

        # Update photon bar
        n = progress.photon_count()
        if progress.photon_target > 0:
            pf = progress.photon_fraction()
            bar_p_fg[0].set_width(pf)
            txt_p.set_text(
                f"{pf*100:.1f}%  {n:,} / "
                f"{progress.photon_target:,}  "
                f"(rem {progress.photon_remaining():,})"
            )
        else:
            bar_p_fg[0].set_width(0)
            txt_p.set_text(f"{n:,} photons  (no target)")
            txt_p.set_color('dimgray')

    ani = animation.FuncAnimation(   # noqa: F841
        fig, update,
        interval=PLOT_INTERVAL_MS,
        blit=False,
        cache_frame_data=False
    )
    plt.tight_layout()
    plt.show()


# =============================================================================
# MAIN
# =============================================================================

def main():
    # ── 1. Interactive configuration ──────────────────────────────────────────
    tau0_s, tau_max_s, acquisition_s, photon_target, port = \
        get_user_parameters()

    # ── 2. Compute correlator levels ──────────────────────────────────────────
    num_levels, tau_covered = compute_num_levels(tau0_s, tau_max_s)

    # ── 3. Connect to the TP1004 ──────────────────────────────────────────────
    print(f"\nOpening connection on port {port}...")
    my_device = pyTempico.TempicoDevice(port)
    my_device.open()
    if not my_device.isOpen():
        raise RuntimeError(f"Could not open connection on {port}.")
    print("Connection open.")

    # Sync device clock -> enables hardware-based elapsed time
    my_device.setDateTime()
    print(f"Device clock synchronized: {my_device.getDateTime(True)}")

    # ── 4. Configure device ───────────────────────────────────────────────────
    print("\nResetting device...")
    my_device.reset()

    my_device.ch1.enableChannel()
    my_device.ch2.disableChannel()
    my_device.ch3.disableChannel()
    my_device.ch4.disableChannel()

    my_device.ch1.setMode(2)           # mode 2: 125 ns - 4 ms range
    my_device.ch1.setNumberOfStops(NUMBER_OF_STOPS)
    my_device.setNumberOfRuns(NUMBER_OF_RUNS)

    print(f"  Mode        : {my_device.ch1.getMode()}")
    print(f"  Stops       : {my_device.ch1.getNumberOfStops()}")
    print(f"  Runs/call   : {my_device.getNumberOfRuns()}")

    # ── 5. Build algorithm objects ────────────────────────────────────────────
    correlator    = MultiTauCorrelator(tau0=tau0_s, num_levels=num_levels)
    reconstructor = PhotonStreamReconstructor(tau0=tau0_s)
    accumulator   = InputAccumulator(correlator, tau0=tau0_s)
    progress      = AcquisitionProgress(my_device, acquisition_s,
                                        photon_target, reconstructor)
    data_queue    = queue.Queue()
    stop_event    = threading.Event()

    # ── 6. Launch threads ─────────────────────────────────────────────────────
    t_prod = threading.Thread(
        target=producer_thread,
        args=(my_device, data_queue, stop_event, reconstructor),
        daemon=True
    )
    t_cons = threading.Thread(
        target=consumer_thread,
        args=(data_queue, accumulator, stop_event),
        daemon=True
    )
    t_prog = threading.Thread(
        target=progress_thread,
        args=(progress, stop_event),
        daemon=True
    )

    progress.start()
    t_prod.start()
    t_cons.start()
    t_prog.start()

    # Auto-stop: checks BOTH conditions every 200 ms
    def _auto_stop():
        while not progress.should_stop():
            time.sleep(0.2)
        stop_event.set()
    threading.Thread(target=_auto_stop, daemon=True).start()

    print(f"\nAcquiring  (close the plot window to stop early)...\n")

    # ── 7. Live plot (blocks until window is closed) ──────────────────────────
    live_acf_plot(correlator, progress, stop_event, tau0_s, tau_max_s)

    # ── 8. Clean shutdown ─────────────────────────────────────────────────────
    stop_event.set()
    t_prod.join(timeout=3)
    t_cons.join(timeout=3)
    t_prog.join(timeout=2)

    # ── 9. Flush last retained bin ────────────────────────────────────────────
    correlator.flush()

    # ── 10. Final summary ────────────────────────────────────────────────────
    elapsed = progress.elapsed()
    print(f"\n{'='*62}")
    print(f"  Acquisition complete")
    print(f"{'='*62}")
    print(f"  Elapsed time          : {elapsed:.2f} s")
    print(f"  Total photons         : {reconstructor.total_photons:,}")
    if photon_target > 0:
        pct = min(100.0, reconstructor.total_photons / photon_target * 100)
        print(f"  Photon target         : {photon_target:,}  ({pct:.1f}% reached)")
    print(f"  Last start event      : {my_device.getLastStart(True)}")
    print(f"  tau_0                 : {tau0_s*1e9:.1f} ns")
    print(f"  Levels used           : {num_levels}")
    print(f"  tau covered           : {tau_covered*1e6:.3f} us")
    print(f"{'='*62}\n")

    # ── 11. Final G(tau) plot ─────────────────────────────────────────────────
    tau, G = correlator.get_acf()
    valid  = np.isfinite(G)

    if valid.any():
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.semilogx(tau[valid], G[valid], 'o-', ms=3, lw=1.2,
                    color='royalblue', label='G(tau)')
        ax.axvline(tau0_s,    color='seagreen', lw=1, ls=':',
                   label=f'tau_0 = {tau0_s*1e9:.0f} ns')
        ax.axvline(tau_max_s, color='tomato',   lw=1, ls='--',
                   label=f'tau_max = {tau_max_s*1e6:.1f} us')
        ax.set_xlabel('Delay time tau (s)')
        ax.set_ylabel('G(tau)')
        ax.set_title(
            f'FCS - Final ACF  |  {reconstructor.total_photons:,} photons  '
            f'|  {elapsed:.1f} s  |  {num_levels} levels'
        )
        ax.legend(fontsize=8)
        ax.grid(True, which='both', alpha=0.3)
        plt.tight_layout()
        plt.savefig('fcs_acf_result.png', dpi=150)
        print("Final ACF saved to fcs_acf_result.png")
        plt.show()
    else:
        print("No valid ACF data. Check that photon signals reached the device.")

    my_device.close()
    print("Connection closed.")


if __name__ == '__main__':
    main()
