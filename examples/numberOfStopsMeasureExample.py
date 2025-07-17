# -*- coding: utf-8 -*-
"""numberOfStopsMeasureExample

    Created on Tue Jul  14 16:42 2025

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

print('\nchanging measurement mode in channel 1 to mode 2')
my_device.ch1.setMode(2)    #default mode is 1, changing to mode 2
#verify
print('my_device.ch1.getMode():',my_device.ch1.getMode())

print('\nchanging number of stops in channel 1 to 5')
my_device.ch1.setNumberOfStops(5)    #default number of stops is 1, changing number of stops to 5
#verify
print('my_device.ch1.getNumberOfStops():',my_device.ch1.getNumberOfStops())

print('\nsending a measure request to device')
data = my_device.measure()   #starts a measurement, and saves response in 'data'
print('measured data, in ps:',data)

print('fetch:',my_device.fetch()) #fetch most recent data
print('\nYou will see 5 stop data per measurement, these stops are captured after the same start signal.')

my_device.close()
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')