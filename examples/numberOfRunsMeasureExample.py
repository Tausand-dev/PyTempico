# -*- coding: utf-8 -*-
"""numberOfRunsMeasureExample

    Created on Tue Jul  14 16:42 2025

    Example script for measuring with a Tausand Tempico device using extended 
    number of runs (1000), and using Mode 2 (125 ns – 4 ms range) on Channel 1.

    This example connects to the Tempico device, configures it to only enable 
    Channel 1, sets the measurement mode to Mode 2, and adjusts the number of 
    runs (measurements) to 1000. It then starts a single measurement operation 
    and reads the resulting data.

    The key feature demonstrated here is the use of `setNumberOfRuns(1000)`, 
    which tells the device to internally perform 1000 measurements in response 
    to a single call to `measure()`. This is ideal for bulk acquisition workflows 
    where multiple time intervals are collected automatically.

    Instructions:
        - Make sure the `pyTempico` package is installed.
        - Replace `'COM5'` with the serial port corresponding to your device.
        - Connect appropriate start/stop signals to the Tempico device.
        - Run the script. If no signals are present, the measurement will return 
          an empty array.

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

print('\nchanging number of runs to 1000, this setting is applied to every channel in the device')
my_device.setNumberOfRuns(1000)    #default number of run is 1, changing to number of run 1000
#verify
print('my_device.getNumberOfRuns():',my_device.getNumberOfRuns())

print('\nsending a measure request to device')
data = my_device.measure()   #starts a measurement, and saves response in 'data'
print('measured data, in ps:',data)

print('fetch:',my_device.fetch()) #fetch most recent data
print('\nIf a measurement was succesful, you will see 1000 different measurements with a single call of the measurement function.')

my_device.close()
if my_device.isOpen():
    print('connection with my_device is open')
else:
    print('connection with my_device is close')