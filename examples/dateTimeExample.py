# -*- coding: utf-8 -*-
"""
dateTimeExample

This script demonstrates how to connect to a Tausand Tempico device and
perform several operations related to time management and measurement flow.

Steps:
- Open connection to the device.
- Reset and configure channels.
- Read and synchronize time.
- Modify allowed datetime range.
- Perform a measurement.

You do **not** need a connected signal to run this example.

Instructions:
1. Ensure `pyTempico` is installed.
2. Replace `'COM5'` with your Tempico port.
3. Run the script.

Author: Joan Amaya, Tausand Electronics
    Email: jamaya@tausand.com
    Website: https://www.tausand.com
"""
import pyTempico

my_port = 'COM5' #change this port to your Tempico device's port

my_device = pyTempico.TempicoDevice(my_port)    #create object

print('opening connection with device in port',my_port)
my_device.open()             #open connection with device
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')

print('\nreseting device. This clears previous measurements, and changes settings to default values.')
my_device.reset()

#Enable channel 1, disable channels 2-4
print('\ndisabling channels 2-4.')
my_device.ch1.enableChannel()   #optional, since enabled by default
my_device.ch2.disableChannel()
my_device.ch3.disableChannel()
my_device.ch4.disableChannel()

print("\nWe want to see the current time in seconds with microsecond resolution. By default, this time is taken when the device is powered on.\n")
print(f"{my_device.getDateTime()}")

print("\nThis time can also be printed in a formatted date style, which will become more useful later on.\n")
print(f"{my_device.getDateTime(True)}")

print("\nThis time can be synchronized by the user, who provides a timestamp in seconds with microsecond resolution.\n")

print("\nHowever, this timestamp must fall within the minimum and maximum limits accepted by the device.\n")
print(f"Maximum value with my_device.getMaximumDatetime(): {my_device.getMaximumDatetime()}")
print(f"Formatted (with True): {my_device.getMaximumDatetime(True)}")
print(f"Minimum value with my_device.getMinimumDatetime(): {my_device.getMinimumDatetime()}")
print(f"Formatted (with True): {my_device.getMinimumDatetime(True)}")

print("\nNow that we know the allowed range, we’ll configure a custom time value.\n")
print("Setting the time using: my_device.setDateTime(3102462800.0)")
my_device.setDateTime(3102462800.0)

print("\nWe can now verify that the time was correctly synchronized.\n")
print(f"Device time via my_device.getDateTime(): {my_device.getDateTime()}")

print("\nAlso we can synchronize the time with our pc, using the same function without parameter.\n")
print("Setting the time using: my_device.setDateTime()")
my_device.setDateTime()

print("\nWe can now verify that the time was correctly synchronized.\n")
print(f"Device time via my_device.getDateTime(): {my_device.getDateTime()}")
print(f"With a date format now my_device.getDateTime(True): {my_device.getDateTime(True)}")


print("\nIf we want to use a timestamp outside the current limits, we can update the allowed range.\n")
print(f"Setting new maximum with my_device.setMaximumDatetime(4103462800.0).")
my_device.setMaximumDatetime(4103462800.0)
print(f"Setting new minimum with my_device.setMinimumDatetime(1576854800.0).")
my_device.setMinimumDatetime(1576854800.0)

print("\nNow we can retrieve the new minimum and maximum values.\n")
print(f"New maximum: my_device.getMaximumDatetime(): {my_device.getMaximumDatetime()}")
print(f"New minimum: my_device.getMinimumDatetime(): {my_device.getMinimumDatetime()}")

print("\nThese values are useful to determine when a start signal was received. We will now perform a measurement — a connected start signal is required.\n")

print("Disabling channels 2–4.")
my_device.ch1.enableChannel()
my_device.ch2.disableChannel()
my_device.ch3.disableChannel()
my_device.ch4.disableChannel()

print("\nStarting a measurement.\n")
my_device.measure()

print("my_device.fetch():")
data = my_device.fetch()
print(data)

print("\nNote that the start time aligns with the synchronized time. Additionally, we can retrieve the time of the last start and the last synchronization (i.e., from setDateTime()).\n")
print(f"Last start via my_device.getLastStart(): {my_device.getLastStart()}")
print(f"Last start (formatted): {my_device.getLastStart(True)}")
print(f"Last synchronization via my_device.getLastSync(): {my_device.getLastSync()}")
print(f"Last synchronization (formatted): {my_device.getLastSync(True)}")

my_device.close()
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')