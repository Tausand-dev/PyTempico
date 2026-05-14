# -*- coding: utf-8 -*-
"""fcsExample

    Acquires photon arrival times from a Tausand Tempico TDC device and
    computes the normalized autocorrelation function G(tau) in real time
    using the multi-tau algorithm. Results are displayed in a live plot
    using PySide2 and pyqtgraph.

    The acquisition loop collects stop-time measurements from the Tempico
    device, reconstructs a continuous relative timeline (ignoring inter-run
    gaps), bins the photon arrivals into intensity bins of duration ``TAU_0``,
    and feeds each bin into a ``MultiTauCorrelator`` instance. The resulting
    G(tau) curve is emitted to the GUI after every batch of runs.

    Instructions:
        - Make sure ``pyTempico`` and ``MultipleTauCorrelator`` are installed
          or available in the Python path.
        - Replace ``MY_PORT`` with the serial port of your Tempico device
          (e.g. ``'COM4'`` on Windows or ``'/dev/ttyUSB0'`` on Linux).
        - Connect a periodic signal to the **start input** and the photon
          detector output to the **stop input** of Channel 1.
        - Adjust ``TAU_0``, ``NUMBER_OF_STOPS``, ``NUMBER_OF_RUNS``, and
          ``TOTAL_SECONDS`` as needed for your experiment.
        - Run the script. The live G(tau) plot will appear immediately and
          update every batch of 100 runs until the acquisition finishes or
          the window is closed.

    | @author: Miguelangel García Castilo, Tausand Electronics
    | mgarcia@tausand.com
    | https://www.tausand.com
"""

import sys
import os

# Add the parent directory to the Python path so that MultipleTauCorrelator
# can be imported even when this script is run from a subdirectory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import pyTempico
from multipleTauCorrelator import MultiTauCorrelator
import numpy as np
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide2.QtCore    import QThread, Signal, QTimer
import pyqtgraph as pg

# ── Configuration ──────────────────────────────────────────────────────────
MY_PORT          = 'COM4'       # Serial port of the Tempico device
NUMBER_OF_STOPS  = 2            # Stop events per run (1–5)
NUMBER_OF_RUNS   = 100          # Runs per measure() call (1–1000)
TOTAL_SECONDS    = 120          # Total acquisition duration in seconds
TAU_0            = 1_000_000    # Base bin size in picoseconds (1 µs)
PLOT_UPDATE_MS   = 500          # GUI refresh interval in milliseconds
# ───────────────────────────────────────────────────────────────────────────


# ── Worker thread: acquisition + correlation ───────────────────────────────
class AcquisitionWorker(QThread):
    """
    Background thread that handles Tempico communication and multi-tau
    correlation. Runs independently of the GUI thread to keep the plot
    responsive during acquisition.

    Signals
    -------
    data_ready : Signal(object, object)
        Emitted after each measure() call with updated (taus_s, g) arrays.
    status_update : Signal(str)
        Emitted after each measure() call with a human-readable status string.
    finished_sig : Signal()
        Emitted once when the acquisition loop exits normally.
    """

    # Emits (taus_s, g) arrays after every batch of runs
    data_ready    = Signal(object, object)
    # Emits a status string for display in the GUI label
    status_update = Signal(str)
    # Emitted once when the acquisition loop finishes
    finished_sig  = Signal()

    def __init__(self, port, number_of_stops, number_of_runs,
                 total_seconds, tau_0_ps):
        super().__init__()
        self.port            = port
        self.number_of_stops = number_of_stops
        self.number_of_runs  = number_of_runs
        self.total_seconds   = total_seconds
        self.tau_0_ps        = tau_0_ps
        # Flag used by stop() to request a clean exit from the run() loop
        self._running        = True

    def stop(self):
        """Request the acquisition loop to exit on the next iteration."""
        self._running = False

    def run(self):
        """
        Main acquisition and correlation loop. Runs in a separate thread.

        Connects to the Tempico device, configures Channel 1, then enters
        a loop that calls measure() repeatedly until the elapsed time exceeds
        ``total_seconds`` or ``stop()`` is called. Each batch of rows is
        processed into intensity bins and fed into the correlator. The
        updated G(tau) curve is emitted after every batch.
        """
        # --- Device connection and configuration ---
        device = pyTempico.TempicoDevice(self.port)
        device.open()
        if not device.isOpen():
            self.status_update.emit(f"ERROR: Could not open port {self.port}")
            return

        self.status_update.emit(f"Connected to {device.getIdn()}")
        # Reset clears all previous measurements and restores default settings
        device.reset()

        # Enable only Channel 1; disable the rest to avoid unwanted triggers
        device.ch1.enableChannel()
        device.ch2.disableChannel()
        device.ch3.disableChannel()
        device.ch4.disableChannel()
        # Mode 2: large measurement range (125 ns – 4 ms start-stop window)
        device.ch1.setMode(2)
        device.ch1.setNumberOfStops(self.number_of_stops)
        device.setNumberOfRuns(self.number_of_runs)

        # Instantiate the multi-tau correlator with the configured bin size
        correlator = MultiTauCorrelator(tau_0=self.tau_0_ps,
                                        num_levels=16, m=16)

        # cursor_ps: running position on the relative timeline (ps).
        # Advances by the last stop time of each run, ignoring inter-run gaps.
        cursor_ps      = 0
        # next_bin_edge: upper boundary of the current intensity bin (ps).
        # When an event crosses this boundary, the bin is closed and a new
        # one starts.
        next_bin_edge  = self.tau_0_ps
        # photons_in_bin: photon counter for the current open bin
        photons_in_bin = 0

        t_start      = time.time()   # Wall-clock time at acquisition start
        call_count   = 0             # Number of measure() calls completed
        total_events = 0             # Total photon events collected so far

        # --- Main acquisition loop ---
        while self._running and (time.time() - t_start) < self.total_seconds:
            # Request one batch of (NUMBER_OF_RUNS × NUMBER_OF_STOPS) measurements
            # Each row has format: [ch, run, start_s, stop_ps1, ..., stop_psN]
            data = device.measure()

            for row in data:
                # Extract stop times in picoseconds (columns 3 onwards)
                stops_ps = row[3:]

                for t_ps in stops_ps:
                    # Compute the absolute position of this event on the
                    # relative timeline by adding the run's cursor offset
                    abs_t = cursor_ps + t_ps

                    # Close all bins that end before this event arrives.
                    # Bins with zero photons (empty bins) are also fed to the
                    # correlator — they carry statistical information about
                    # periods of silence.
                    while abs_t >= next_bin_edge:
                        correlator.process_datum(photons_in_bin)
                        photons_in_bin = 0
                        next_bin_edge += self.tau_0_ps

                    # Register this photon in the current open bin
                    photons_in_bin += 1
                    total_events   += 1

                # Advance the timeline cursor to the last stop of this run.
                # The gap between the last stop and the next run's first stop
                # is intentionally ignored (Option B: relative timeline).
                cursor_ps += stops_ps[-1]

            call_count += 1
            elapsed = time.time() - t_start

            # Retrieve the current ACF and emit it to the GUI for plotting
            taus, g = correlator.get_correlation_curve()
            if len(taus) > 0:
                # Convert lag times from picoseconds to seconds before emitting
                self.data_ready.emit(taus * 1e-12, g)

            self.status_update.emit(
                f"calls: {call_count} | events: {total_events} | "
                f"elapsed: {elapsed:.1f} s"
            )

        # Flush the last partially filled bin into the correlator
        correlator.process_datum(photons_in_bin)
        taus, g = correlator.get_correlation_curve()
        if len(taus) > 0:
            self.data_ready.emit(taus * 1e-12, g)

        device.close()
        self.status_update.emit("Acquisition finished.")
        self.finished_sig.emit()


# ── Main window ────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    """
    Main application window. Contains a status label and a pyqtgraph
    PlotWidget that displays the live G(tau) autocorrelation curve.
    Starts the AcquisitionWorker thread on construction and stops it
    cleanly when the window is closed.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FCS — Real-time Autocorrelation")
        self.resize(900, 550)

        # Central widget and vertical layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Status label: shows acquisition progress from the worker thread
        self.status_label = QLabel("Starting acquisition...")
        self.status_label.setStyleSheet("font-size: 11px; color: #444;")
        layout.addWidget(self.status_label)

        # --- pyqtgraph plot widget ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left',   'G(τ)')
        self.plot_widget.setLabel('bottom', 'τ', units='s')
        self.plot_widget.setTitle('Autocorrelation Function — Tempico FCS')
        # Logarithmic x-axis: standard presentation for FCS curves
        self.plot_widget.setLogMode(x=True, y=False)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()

        # Horizontal dashed reference line at G = 1 (uncorrelated baseline)
        ref_line = pg.InfiniteLine(
            pos=1.0, angle=0,
            pen=pg.mkPen('gray', width=1, style=pg.QtCore.Qt.DashLine)
        )
        self.plot_widget.addItem(ref_line)

        # Scatter plot curve: updated in real time by update_plot()
        self.curve = self.plot_widget.plot(
            [], [],
            pen=None,
            symbol='o',
            symbolSize=5,
            symbolBrush='steelblue',
            symbolPen=None,
            name='G(τ) measured'
        )

        layout.addWidget(self.plot_widget)

        # --- Acquisition worker ---
        # Runs in a separate QThread to avoid blocking the GUI event loop
        self.worker = AcquisitionWorker(
            port            = MY_PORT,
            number_of_stops = NUMBER_OF_STOPS,
            number_of_runs  = NUMBER_OF_RUNS,
            total_seconds   = TOTAL_SECONDS,
            tau_0_ps        = TAU_0,
        )
        # Connect worker signals to GUI slots
        self.worker.data_ready.connect(self.update_plot)
        self.worker.status_update.connect(self.update_status)
        self.worker.finished_sig.connect(self.on_finished)
        self.worker.start()

    def update_plot(self, taus_s, g):
        """Update the scatter plot with the latest G(tau) values."""
        # pyqtgraph requires strictly positive x values when logMode x=True
        mask = taus_s > 0
        self.curve.setData(taus_s[mask], g[mask])

    def update_status(self, msg):
        """Update the status label with the latest acquisition progress."""
        self.status_label.setText(msg)

    def on_finished(self):
        """Append a completion marker to the status label."""
        self.status_label.setText(
            self.status_label.text() + "  ✓ Done."
        )

    def closeEvent(self, event):
        """Stop the worker thread cleanly before closing the window."""
        # Signal the worker loop to exit, then wait for the thread to finish
        self.worker.stop()
        self.worker.wait()
        event.accept()


# ── Entry point ────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    # Enable antialiasing for smoother scatter plot markers
    pg.setConfigOptions(antialias=True)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()