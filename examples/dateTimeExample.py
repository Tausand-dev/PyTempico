# -*- coding: utf-8 -*-
"""modeTwoMultiStopExample

    Created on Tue May  7 11:42 2024

    Example script for measuring with a Tausand Tempico device using Mode 2 
    (125 ns – 4 ms range) on Channel 1, with multiple stops per measurement.

    This example connects to the Tempico device, enables only Channel 1, sets 
    the measurement mode to Mode 2, and changes the number of stops to 5. It 
    then starts a measurement and prints the result.

    The key feature demonstrated here is the use of `setNumberOfStops(5)`, 
    which configures the device to collect **5 stop events** after a single 
    start signal during each measurement cycle. This is useful for analyzing 
    multiple photon arrivals or signal repetitions after a common trigger.

    Instructions:
        - Make sure the `pyTempico` package is installed.
        - Replace `'COM5'` with the serial port corresponding to your device.
        - Connect a periodic signal to the **start input**, and the signal to 
          be measured to the stop input of Channel 1.
        - Run the script. If no signals are received, the measurement will 
          return an empty array.

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

print("\nIf we want to use a timestamp outside the current limits, we can update the allowed range.\n")
print(f"Setting new maximum with my_device.setMaximumDatetime(4103462800.0): {my_device.setMaximumDatetime(4103462800.0)}")
print(f"Setting new minimum with my_device.setMinimumDatetime(1576854800.0): {my_device.setMinimumDatetime(1576854800.0)}")

print("\nNow we can retrieve the new minimum and maximum values.\n")
print(f"New maximum: my_device.getMaximumDatetime(): {my_device.getMaximumDatetime()}")
print(f"New minimum: my_device.getMinimumDatetime(): {my_device.getMinimumDatetime()}")

print("\nThese values are useful to determine when a start signal was received. We will now perform a measurement — a connected signal is not required.\n")

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