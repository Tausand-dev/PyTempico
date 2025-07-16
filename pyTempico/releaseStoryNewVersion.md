# Release Notes 1.2.0 – July 2025

## New Features

- Added time utility functions:
  - Retrieve the **elapsed time in seconds (with microsecond resolution)** since the PC was powered on.
  - **Synchronize internal time** with a custom reference value provided by the user.
  - Configure **minimum and maximum time range** values.
  - Retrieve time either as **seconds** or **formatted date**.
- Channel access has been simplified: channels can now be accessed **directly from the device class**, instead of needing a dedicated class per channel.
- Added support to retrieve the **manufacturer's serial number** of the device.

---

# Release Notes 1.1.1 – March 2025

## Bug fixed

- Fixed compatibilty with macOS

---

# Release Notes 1.1.0 – February 2025

## New Features

- Devices can now **auto-detect available ports** and identify which ones are connected to a Tempico device.
- Added function to **validate if a given port corresponds to a Tempico device**.
- Implemented **hardware self-test** capability for diagnostic purposes.
- Added support for **aborting ongoing measurements** safely and cleanly.

---

# Release Notes 1.0.1 – November 2024

## Bug Fixed

- Fixed bug in getFirmare() method

---

# Release Notes 1.0.0 – February 2024

## Initial Release

- Full support for **serial communication** with Tempico devices.
- Core device configuration functions:
  - Set the **number of stops**, **average cycles**, and **measurement runs**.
  - Configure **stop mask** and **edge type** per stop channel.
  - Configure **edge type for the start** signal.
  - Change **measurement mode**.
  - Set **voltage threshold** for signal detection.
- Device I/O:
  - **Open connection** via a specified serial port.
  - **Send commands** to the device and **check pending messages**.
  - **Wait for responses** and **retrieve the last measurement**.
  - Query the device's **IDN** and **firmware version**.
- Utility functions to **read and view device configuration**.
