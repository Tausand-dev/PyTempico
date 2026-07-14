# -*- coding: utf-8 -*-
"""g2Example

    Acquires start-stop time delays from a Tausand Tempico TDC device and
    computes the second-order correlation function g²(τ) in real time using
    a normalized delay histogram. Results are displayed in a live plot using
    PySide2 and pyqtgraph.

    Supported devices
    -----------------
    TP1204
        Delivers signed tau values (start may arrive after stop), so the
        histogram spans the symmetric window [-WINDOW_NS, +WINDOW_NS].
        No external delay line is required.
    TP1004
        Delivers only positive tau values (start always arrives before stop).
        The histogram spans the asymmetric window [0, +WINDOW_NS].
        An external delay line is required if you need to observe tau < 0.

    Instructions:
        - Make sure ``pyTempico`` and ``g2Algorithm`` (G2Computer) are
          installed or available in the Python path.
        - Set ``DEVICE_MODEL`` to ``'TP1204'`` or ``'TP1004'`` to match
          your hardware.
        - Replace ``PORT`` with the serial port of your Tempico device
          (e.g. ``'COM4'`` on Windows or ``'/dev/ttyUSB0'`` on Linux).
        - Connect both outputs of your beam splitter to the START and STOP
          inputs of the selected channel.
        - Adjust ``BIN_NS``, ``WINDOW_NS``, ``N_RUNS``, and ``MODE`` as
          needed for your experiment.
        - Run the script. The live g²(τ) plot will appear immediately and
          update after every acquisition batch until the window is closed.

    | @author: Miguelangel García Castilo, Tausand Electronics
    |  mgarcia@tausand.com 
    | https://www.tausand.com
"""

# ── Imports ────────────────────────────────────────────────────────────────
import sys
import io
import os
import csv
import time

import numpy as np

from PySide2.QtCore    import Qt, QThread, Signal, Slot
from PySide2.QtWidgets import QApplication, QMainWindow

import pyqtgraph as pg

import pyTempico

from g2Algorithm import G2Computer


# ── Configuration ──────────────────────────────────────────────────────────
# Device
DEVICE_MODEL = "TP1204"     # 'TP1204' (signed tau) or 'TP1004' (positive tau only)
PORT         = "COM5"       # Serial port where the Tempico device is connected
N_RUNS       = 20           # Number of runs per acquisition batch

# Channel
CHANNEL       = 1                               # TDC channel: 1=A | 2=B | 3=C | 4=D
CHANNEL_LABEL = chr(ord('A') + CHANNEL - 1)    # Derived label: 'A', 'B', 'C', or 'D'

# TDC mode (TP1204 only; the TP1004 has a fixed range):
#   1 = range -200 ns … +300 ns  (recommended for HBT / single photons)
#   2 = range  -50 ns … +4 ms    (for coincidences with larger delays)
MODE = 1

# Histogram
BIN_NS    = 15.0    # Bin width in nanoseconds
WINDOW_NS = 180.0   # Half-window (ns): histogram spans [-W, +W] for TP1204
                    # or [0, +W] for TP1004

# Signal source
#   'external' -> physical connector on the Tempico device
#   'internal' -> Tempico internal generator (TP12 series only)
START_SRC   = "external"
STOP_SRC    = "external"
INT_FREQ_HZ = 100_000   # Hz -- only used when START_SRC == 'internal'

# TP1204 / TP1004 sentinel and threshold values
OVERFLOW_PARAMETER        = -1_000_000  # Returned by pyTempico when no valid stop
OUT_OF_RANGE_THRESHOLD_PS = 800_000     # 800 ns in ps; triggers a warning if exceeded
# ───────────────────────────────────────────────────────────────────────────


# ── Worker thread: device acquisition ──────────────────────────────────────
class HBTWorker(QThread):
    """
    Background thread that handles Tempico communication and g²(τ)
    histogram accumulation. Runs independently of the GUI thread to keep
    the plot responsive during acquisition.

    The active TDC channel is selected by the CHANNEL constant above.
    Device-specific behaviour (signed vs. positive-only tau) is controlled
    by the DEVICE_MODEL constant:
        - TP1204: signed tau, symmetric histogram window.
        - TP1004: positive tau only, asymmetric histogram window.

    Signals
    -------
    data_ready : Signal(object, object, int, float, float)
        Emitted after each batch with (centres, g2, n_events,
        rate_start, rate_stop).
    status_update : Signal(str)
        Emitted after each batch with a human-readable status string.
    color_value : Signal(int)
        Severity indicator emitted with every status update:
        1 = OK, 2 = error, 3 = warning.
    dialog_signal : Signal(str)
        Emitted when more than 60% of measurements on a channel are
        out of range, carrying the channel label as a string.
    model_ready : Signal(str)
        Emitted once after connection with the device model identifier
        returned by device.getModelIdn().
    finished_sig : Signal()
        Emitted once when the acquisition loop exits normally.
    """

    data_ready    = Signal(object, object, int, float, float)
    status_update = Signal(str)
    color_value   = Signal(int)
    dialog_signal = Signal(str)
    model_ready   = Signal(str)
    finished_sig  = Signal()

    def __init__(self):
        super().__init__()

        self._running = True

        # -- Out-of-range / dialog state -------------------------------------
        self.outOfRange     = 0
        self.sentinelDialog = False

        # Failure-control counters (ThreadStartStop pattern)
        self.channelsNM            = []
        self.noMeasurementsSequent = 0
        self.noAbortsSequent       = 0
        self.consecutiveErrors     = 0
        self.openDialog            = False

        # -- G2Computer: owns the histogram and g²(τ) math ------------------
        # positive_only=True for TP1004 (no negative tau values)
        positive_only = (DEVICE_MODEL.upper() == "TP1004")
        self.g2 = G2Computer(BIN_NS, WINDOW_NS, N_RUNS,
                             positive_only=positive_only)

        self.t_start = None
        self.device  = None

        # Saved device settings (restored after a hardware reset)
        self.numberRunsSetting = N_RUNS
        self.modeCh            = MODE
        self.numberStopsCh     = 1

    def stop(self):
        """Request the acquisition loop to exit on the next iteration."""
        self._running = False

    @Slot()
    def dialogClosed(self):
        """Acknowledge the out-of-range dialog so the worker can continue."""
        self.openDialog = False

    # ── run ───────────────────────────────────────────────────────────────
    def run(self):
        """
        Main acquisition loop. Runs in a separate thread.

        Connects to the Tempico device, configures the selected channel,
        then calls getMeasurements() in a tight loop until stop() is called.
        Emits finished_sig when the loop exits.
        """
        self.device = pyTempico.TempicoDevice(PORT)
        self.device.open()

        if not self.device.isOpen():
            self.status_update.emit(f"ERROR: could not open {PORT}")
            self.color_value.emit(2)
            self.finished_sig.emit()
            return

        model = self.device.getModelIdn()
        self.model_ready.emit(model)
        self.status_update.emit(f"Connected: {self.device.getIdn()}")
        self.device.reset()

        # Enable only the selected channel; disable the rest
        for _n in (1, 2, 3, 4):
            _ch_obj = getattr(self.device, f'ch{_n}')
            if _n == CHANNEL:
                _ch_obj.enableChannel()
            else:
                _ch_obj.disableChannel()

        _active_ch = getattr(self.device, f'ch{CHANNEL}')

        # Mode is settable on the TP1204; the TP1004 has a fixed range
        if DEVICE_MODEL.upper() == "TP1204":
            _active_ch.setMode(MODE)

        _active_ch.setNumberOfStops(1)
        _active_ch.setAverageCycles(1)
        _active_ch.setStopMask(-0.25)       # Minimum mask on TP12 series
        self.device.setNumberOfRuns(N_RUNS)

        # Signal source configuration
        if START_SRC == "internal":
            self.device.setGeneratorFrequency(INT_FREQ_HZ)
            self.device.setStartInternalSource(1)
        else:
            self.device.setStartExternalSource(1)

        if STOP_SRC == "internal":
            self.device.setStopInternalSource(1)
        else:
            self.device.setStopExternalSource(1)

        # Save current settings so they can be restored after a device reset
        self._saveCurrentSettings()

        self.t_start = time.time()

        # --- Main acquisition loop ---
        while self._running:
            self.getMeasurements()
            time.sleep(0.05)

        # Clean shutdown: re-enable all channels before closing
        try:
            for _n in (1, 2, 3, 4):
                getattr(self.device, f'ch{_n}').enableChannel()
            self.device.close()
        except Exception:
            pass

        t_elapsed = time.time() - self.t_start if self.t_start else 0
        self.status_update.emit(
            f"Acquisition finished. "
            f"Events: {self.g2.total_events} | Time: {t_elapsed:.1f} s"
        )
        self.finished_sig.emit()

    # ── getMeasurements ───────────────────────────────────────────────────
    def getMeasurements(self):
        """
        Acquire one batch from the Tempico device and feed valid tau values
        to G2Computer.

        Row format returned by pyTempico:
            [ch, run, start_time_us, stop_ps1]

        Conversion:
            tau [ns] = stop_ps1 / 1000

        For the TP1204 the sign is preserved (negative tau is native; no
        external delay line needed). For the TP1004 all values are positive
        by design; negative results indicate noise and are discarded by
        G2Computer.accumulate() via the positive_only flag.

        Out-of-range events (|stop_ps1| > OUT_OF_RANGE_THRESHOLD_PS) are
        counted and trigger a warning dialog if they exceed 60% of all
        events, but are still passed to the histogram.
        """
        taus_batch_ns = []

        try:
            # Capture stdout to suppress pyTempico console output
            originalConsole = sys.stdout
            sys.stdout      = io.StringIO()
            measurement     = self.device.measure()
            printedOutput   = sys.stdout.getvalue()
            sys.stdout      = originalConsole

            # If a timeout was reported, keep fetching until the response is stable
            if "Timeout reached" in printedOutput:
                finishedMeasurement = False
                while not finishedMeasurement:
                    time.sleep(1)
                    newFetch = self.device.fetch()
                    if newFetch == measurement:
                        finishedMeasurement = True
                        measurement = newFetch
                    else:
                        measurement = newFetch

            # Handle empty measurement (ThreadStartStop pattern)
            if not measurement and self.noMeasurementsSequent < 3:
                self.noMeasurementsSequent += 1
            elif not measurement and self.noAbortsSequent >= 10:
                # Too many consecutive failures: reset and restore settings
                self.device.reset()
                self._applyCurrentSettings()
                QThread.msleep(20)
            elif not measurement and self.noMeasurementsSequent >= 3:
                self.noAbortsSequent += 1
                self.device.abort()

            # --- Process each row in the batch ---
            if measurement:
                self.noAbortsSequent       = 0
                self.noMeasurementsSequent = 0

                for run_row in measurement:
                    if not run_row:
                        # Empty row means no START signal was detected this run
                        if "Start" not in self.channelsNM:
                            self.channelsNM = ["Start"]
                        continue

                    ch = run_row[0]
                    if ch != CHANNEL:
                        continue    # Ignore data from non-selected channels

                    if "Start" in self.channelsNM:
                        self.channelsNM.remove("Start")

                    # Number of valid stops in this row
                    n_stops_row = self._getRange(run_row, self.numberStopsCh)

                    for i in range(n_stops_row):
                        raw_ps = run_row[3 + i]     # Stop time in picoseconds

                        # Discard the overflow sentinel returned by pyTempico
                        if raw_ps == OVERFLOW_PARAMETER:
                            _ch_label = f"Ch{CHANNEL}"
                            if _ch_label not in self.channelsNM:
                                self.channelsNM.append(_ch_label)
                            continue

                        _ch_label = f"Ch{CHANNEL}"
                        if _ch_label in self.channelsNM:
                            self.channelsNM.remove(_ch_label)

                        self.g2.n_starts += 1

                        # Convert ps → ns (sign preserved for TP1204;
                        # TP1004 only delivers positive values)
                        tau_ns = raw_ps / 1e3

                        # Out-of-range detection (warning only; not discarded)
                        if abs(raw_ps) > OUT_OF_RANGE_THRESHOLD_PS:
                            self.outOfRange += 1
                            if (self.g2.n_starts > 10 and
                                    (self.outOfRange / self.g2.n_starts) > 0.6 and
                                    not self.sentinelDialog):
                                self.sentinelDialog = True
                                self.openDialog     = True
                                self.dialog_signal.emit(f"channel {CHANNEL_LABEL}")
                                # Block until the user acknowledges the warning
                                while self.openDialog:
                                    time.sleep(1)
                                # Re-read mode in case the user changed it
                                if DEVICE_MODEL.upper() == "TP1204":
                                    self.modeCh = getattr(
                                        self.device, f'ch{CHANNEL}'
                                    ).getMode()

                        self.g2.n_stops      += 1
                        self.g2.total_events += 1

                        if self.g2.isBatched:
                            taus_batch_ns.append(tau_ns)
                        else:
                            self.g2.accumulate([tau_ns])

            else:
                if "Start" not in self.channelsNM:
                    self.channelsNM = ["Start"]

            # End of batch: flush buffered taus and compute g²(τ)
            if self.g2.isBatched and taus_batch_ns:
                self.g2.accumulate(taus_batch_ns)

            t_elapsed = time.time() - self.t_start if self.t_start else 1e-9
            g2, rate_start, rate_stop, baseline = self.g2.compute_g2(t_elapsed)
            self.data_ready.emit(
                self.g2.centres, g2, self.g2.total_events, rate_start, rate_stop
            )

            # Emit status and color severity
            if self.channelsNM:
                self.color_value.emit(3)
                self.status_update.emit(
                    "No signal on: " + ", ".join(self.channelsNM)
                )
            else:
                self.color_value.emit(1)
                self.status_update.emit(
                    f"Measuring | events: {self.g2.total_events} | "
                    f"t: {t_elapsed:.1f} s | "
                    f"R_start: {rate_start:.0f} cps | "
                    f"R_stop: {rate_stop:.0f} cps | "
                    f"baseline: {baseline:.1f} counts/bin"
                )

            self.consecutiveErrors = 0

        except Exception as e:
            sys.stdout = sys.__stdout__
            self.consecutiveErrors += 1
            if self.consecutiveErrors > 10:
                self.stop()
            self.status_update.emit(f"Error: {e}")
            self.color_value.emit(2)

    # ── helpers ───────────────────────────────────────────────────────────
    def _getRange(self, run, stop_number):
        """
        Return the number of valid stops present in a measurement row.

        Row format: [ch, run, start_time_us, stop_ps1, ...].
        Columns 0–2 are metadata; stop values start at index 3.
        """
        total_len = len(run)
        if total_len >= 4:
            return min(total_len - 3, stop_number)
        return 0

    def _saveCurrentSettings(self):
        """Read and store the current device settings for later restoration."""
        _ch = getattr(self.device, f'ch{CHANNEL}')
        self.numberRunsSetting = self.device.getNumberOfRuns()
        self.numberStopsCh     = _ch.getNumberOfStops()
        if DEVICE_MODEL.upper() == "TP1204":
            self.modeCh = _ch.getMode()

    def _applyCurrentSettings(self):
        """Restore previously saved device settings after a hardware reset."""
        _ch = getattr(self.device, f'ch{CHANNEL}')
        self.device.setNumberOfRuns(self.numberRunsSetting)
        _ch.setNumberOfStops(self.numberStopsCh)
        if DEVICE_MODEL.upper() == "TP1204":
            _ch.setMode(self.modeCh)
        for _n in (1, 2, 3, 4):
            _ch_obj = getattr(self.device, f'ch{_n}')
            if _n == CHANNEL:
                _ch_obj.enableChannel()
            else:
                _ch_obj.disableChannel()


# ── Plot window ────────────────────────────────────────────────────────────
class HBTPlotWindow(QMainWindow):
    """
    Minimal real-time plot window for g²(τ).

    Contains nothing but a pyqtgraph PlotWidget: no buttons, no status
    bar, no spin boxes. The histogram curve is refreshed every time the
    worker thread emits new data through the data_ready signal.
    Saves tau/g²(τ) data to a CSV file when the window is closed.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            f"g²(τ)  HBT  --  Tausand Tempico {DEVICE_MODEL}"
            f"  (channel {CHANNEL_LABEL})"
        )
        self.resize(1000, 650)

        pg.setConfigOptions(antialias=True)

        self.plot = pg.PlotWidget()
        self.plot.setBackground('w')
        self.plot.setLabel('left',   'g\u207d\u00b2\u207e(\u03c4)',
                           color='#222222', size='12pt')
        self.plot.setLabel('bottom', 'Delay  \u03c4  (ns)',
                           color='#222222', size='12pt')
        self.plot.setTitle(
            f'Second-order correlation function  g\u207d\u00b2\u207e(\u03c4)'
            f'  --  Tausand Tempico {DEVICE_MODEL}',
            color='#111111', size='11pt'
        )
        self.plot.showGrid(x=True, y=True, alpha=0.35)
        self.plot.addLegend(offset=(10, 10))

        # Reference lines
        self.plot.addItem(pg.InfiniteLine(
            pos=1.0, angle=0,
            pen=pg.mkPen('#555555', width=1.4, style=Qt.DashLine),
            label='g\u00b2=1',
            labelOpts={'color': '#555555', 'position': 0.05}
        ))
        self.plot.addItem(pg.InfiniteLine(
            pos=0.5, angle=0,
            pen=pg.mkPen('#aaaaaa', width=1.0, style=Qt.DotLine),
            label='g\u00b2=0.5',
            labelOpts={'color': '#aaaaaa', 'position': 0.08}
        ))
        # tau = 0 vertical line (only meaningful for the symmetric TP1204 window)
        if DEVICE_MODEL.upper() == "TP1204":
            self.plot.addItem(pg.InfiniteLine(
                pos=0.0, angle=90,
                pen=pg.mkPen('#e74c3c', width=1.0, style=Qt.DashLine),
                label='\u03c4=0',
                labelOpts={'color': '#e74c3c', 'position': 0.95}
            ))

        # Step-histogram curve for g²(τ)
        self.curve = self.plot.plot(
            [], [],
            stepMode='center',
            fillLevel=0,
            brush=pg.mkBrush(41, 128, 185, 100),
            pen=pg.mkPen('#2980b9', width=1.5),
            name=f'g\u00b2(\u03c4)  --  {DEVICE_MODEL} channel {CHANNEL_LABEL}'
        )

        self.setCentralWidget(self.plot)

        # Reference to the worker thread (assigned from main) and last data
        # buffers used for CSV export when the window is closed
        self.worker       = None
        self.last_centres = np.array([])
        self.last_g2      = np.array([])

    # ── Slots ─────────────────────────────────────────────────────────────
    @Slot(str)
    def update_model_title(self, model_str):
        """
        Connected to HBTWorker.model_ready. Replaces the placeholder device
        name with the actual model identifier returned by device.getModelIdn(),
        both in the window title and in the plot title.
        """
        self.setWindowTitle(
            f"g\u00b2(\u03c4)  HBT  --  {model_str}  (channel {CHANNEL_LABEL})"
        )
        self.plot.setTitle(
            f"Second-order correlation function  g\u207d\u00b2\u207e(\u03c4)"
            f"  --  {model_str}",
            color='#111111', size='11pt'
        )

    @Slot(object, object, int, float, float)
    def update_plot(self, centres, g2, n_events, rate_s, rate_p):
        """
        Redraw the histogram curve every time HBTWorker emits new data.

        stepMode='center' in pyqtgraph requires n+1 edges for n bin values,
        built as:
            edges = [centres[0] - bin/2, centres[1] + bin/2, ...,
                     centres[-1] + bin/2]
        """
        if len(centres) == 0 or len(g2) == 0:
            return

        centres = np.asarray(centres)
        g2      = np.asarray(g2)

        bin_ns = float(centres[1] - centres[0]) if len(centres) > 1 else BIN_NS
        edges  = np.concatenate([[centres[0] - bin_ns / 2], centres + bin_ns / 2])
        self.curve.setData(edges, g2)

        # Save the latest tau/g²(τ) arrays for CSV export on close
        self.last_centres = centres
        self.last_g2      = g2

        # g²(0): bin closest to tau = 0
        z_idx   = int(np.argmin(np.abs(centres)))
        g2_zero = float(g2[z_idx])

        # Auto Y-range with 15% margin
        g2_max = max(float(np.max(g2)) * 1.15, 1.5) if len(g2) else 1.5
        self.plot.setYRange(0, g2_max)

        # Compact statistics in the window title
        self.setWindowTitle(
            f"g\u00b2(\u03c4) HBT  --  g2(0)={g2_zero:.3f} | "
            f"events={n_events:,} | "
            f"R_start={rate_s:.0f} cps | R_stop={rate_p:.0f} cps"
        )

    def closeEvent(self, event):
        """
        Called automatically when the user clicks the close button (X).

        1. Saves the latest tau/g²(τ) data to a CSV file.
        2. Stops the HBTWorker thread cleanly.
        3. Allows the window to close normally.
        """
        self._save_g2_data()

        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)  # Wait up to 3 s for the thread to finish

        super().closeEvent(event)

    def _save_g2_data(self):
        """Write the latest tau_ns / g²(τ) columns to a timestamped CSV file."""
        if self.last_centres is None or len(self.last_centres) == 0:
            print("\n[INFO] No g²(τ) data to save yet.")
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename  = f"g2_data_{timestamp}.csv"
        filepath  = os.path.abspath(filename)

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["tau_ns", "g2"])
            for tau, g2_val in zip(self.last_centres, self.last_g2):
                writer.writerow([f"{tau:.6f}", f"{g2_val:.6f}"])

        print(f"\n[INFO] g²(τ) data saved to: {filepath}")


# ── Signal handlers (terminal output) ─────────────────────────────────────
@Slot(object, object, int, float, float)
def on_data_ready(centres, g2, n_events, rate_s, rate_p):
    """Print g²(0) and basic statistics each time a batch is processed."""
    if len(centres) == 0 or len(g2) == 0:
        return
    z_idx   = int(np.argmin(np.abs(centres)))
    g2_zero = float(g2[z_idx])
    print(
        f"  events: {n_events:>8,} | "
        f"g2(0): {g2_zero:.4f} | "
        f"R_start: {rate_s:,.0f} cps | "
        f"R_stop: {rate_p:,.0f} cps"
    )

@Slot(str)
def on_status(msg):
    """Print status messages emitted by the worker."""
    print(f"[status] {msg}")

@Slot(int)
def on_color(code):
    """Print a severity indicator: 1=OK, 2=ERROR, 3=WARNING."""
    labels = {1: "OK", 2: "ERROR", 3: "WARNING"}
    print(f"[{labels.get(code, '?')}]")

@Slot(str)
def on_dialog(channel_name):
    """
    Called when more than 60% of measurements on a channel are out of range.
    Prints a warning and acknowledges immediately so the worker can continue.
    """
    print(
        f"\n[WARNING] More than 60% of measurements on {channel_name} "
        "are out of range.\n"
        "Consider switching TDC mode (1 ↔ 2) or adjusting the signal "
        "time window.\n"
    )
    # Acknowledge so the worker thread is not blocked waiting for a dialog
    worker.dialogClosed()

@Slot()
def on_finished():
    """Called when the worker finishes; exits the Qt event loop."""
    print("\nAcquisition finished. Exiting.")
    QApplication.instance().quit()


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Plot window: only the g²(τ) histogram, no control panel
    window = HBTPlotWindow()
    window.show()

    worker = HBTWorker()
    window.worker = worker  # Reference stored so closeEvent can stop the thread

    # Connect worker signals to the terminal handlers and the live plot
    worker.data_ready.connect(on_data_ready)
    worker.data_ready.connect(window.update_plot)
    worker.status_update.connect(on_status)
    worker.color_value.connect(on_color)
    worker.dialog_signal.connect(on_dialog)
    worker.model_ready.connect(window.update_model_title)
    worker.finished_sig.connect(on_finished)

    print(f"Starting HBT acquisition ({DEVICE_MODEL}) -- press Ctrl+C to stop.\n")
    worker.start()

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        worker.stop()
        worker.wait(3000)
        sys.exit(0)