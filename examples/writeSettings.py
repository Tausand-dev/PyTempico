# -*- coding: utf-8 -*-
"""writeSettings

    Created on Tue Jul  14 16:42 2025

    This example connects to a Tausand Tempico device and demonstrates how to 
    read and modify its basic settings, including average cycles, number of stops, 
    and stop mask — both using direct channel access and the main device interface.

    Instructions:
        - Make sure the pyTempico package is installed.
        - Replace 'COM5' with the appropriate serial port for your Tempico device.
        - Run the script.

    Author: Joan Amaya, Tausand Electronics
    Email: jamaya@tausand.com
    Website: https://www.tausand.com
"""

import pyTempico

# Set your device port here
my_port = 'COM5'
my_device = pyTempico.TempicoDevice(my_port)

print(f"\nOpening connection on port {my_port}...")
my_device.open()

if my_device.isOpen():
    print("Device connection is open.")
else:
    print("Failed to open device connection.")

# Reset to default settings before making changes
print("\nResetting device to default settings...")
my_device.reset()

# Read initial settings
print("\n[1] Reading default settings with my_device.getSettings():")
settings = my_device.getSettings()
print(settings)

# Modify average cycles (Channel 1)
print("\n[2] Setting average cycles on Channel 1 using direct channel method (Channel 1 → 4 cycles):")
my_device.ch1.setAverageCycles(4)
print(f"New value: {my_device.ch1.getAverageCycles()}")

# Reset and apply the same setting using device-level method
print("\nResetting...")
my_device.reset()
print("\n[3] Setting average cycles via device method (Channel 1 → 8 cycles):")
my_device.setAverageCycles(1, 8)
print(f"Verified: {my_device.getAverageCycles(1)}")

# Modify number of stops
print("\nResetting...")
my_device.reset()
print("\n[4] Setting number of stops on Channel 1 using direct method (Channel 1 → 5 stops):")
my_device.ch1.setNumberOfStops(5)
print(f"New value: {my_device.ch1.getNumberOfStops()}")

# Reset and set using device method
print("\nResetting...")
my_device.reset()
print("\n[5] Setting number of stops via device method (Channel 1 → 4 stops):")
my_device.setNumberOfStops(1, 4)
print(f"Verified: {my_device.getNumberOfStops(1)}")

# Modify stop mask
print("\nResetting...")
my_device.reset()
print("\n[6] Setting stop mask on 1000 us in Channel 1 using direct method (Channel 1 → 1000):")
my_device.ch1.setStopMask(1000)
print(f"New value: {my_device.ch1.getStopMask()}")

# Reset and set using device method
print("\nResetting...")
my_device.reset()
print("\n[7] Setting stop mask on 2000 us via device method (Channel 1 → 2000):")
my_device.setStopMask(1, 2000)
print(f"Verified: {my_device.getStopMask(1)}")

# Close connection
print(f"\nClosing connection on port {my_port}...")
my_device.close()

if my_device.isOpen():
    print("Connection is still open.")
else:
    print("Connection closed successfully.")
